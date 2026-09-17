import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Play, Loader2, CheckCircle2, XCircle, ShieldAlert, Clock, 
  Wrench, ChevronRight, FileDown, AlertTriangle, Send, ShieldCheck,
  FileText, Database, ShieldX, KeyRound, History
} from 'lucide-react';

// ── Types ────────────────────────────────────────────────────

interface EvidenceRecord {
  source_doc?: string;
  filename?: string;
  page?: number | string;
  chunk_index?: number;
  score: number;
  text?: string;
  snippet?: string;
  section?: string;
}

interface EvidenceVerification {
  verdict: 'SUFFICIENT' | 'INSUFFICIENT' | 'MISSING';
  records?: EvidenceRecord[];
  max_score: number;
  min_score: number;
  avg_score: number;
  details: string;
  requires_override: boolean;
  evaluated_at?: string;
}

interface ApprovalRequest {
  request_id: string;
  task_id: string;
  tool_name: string;
  tool_args: Record<string, any>;
  risk_level: string;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  created_at: string;
  expires_at: string;
  decided_at?: string;
  decided_by?: string;
  override: boolean;
  override_reason?: string;
  evidence_verification?: EvidenceVerification;
}

interface AgentStep {
  step_id: string;
  state: string;
  timestamp: string;
  thought?: string;
  tool_call?: any;
  tool_result?: string;
  evidence?: EvidenceRecord[];
  approval_request?: ApprovalRequest;
  error?: string;
}

interface AgentTask {
  task_id: string;
  prompt: string;
  status: string;
  steps: AgentStep[];
  final_result?: string;
  selected_model?: string;
  approval_request?: ApprovalRequest;
}

interface Tool {
  name: string;
  description: string;
}

interface AuditEntry {
  entry_id: string;
  timestamp: string;
  action: string;
  task_id: string;
  actor: string;
  tool_name?: string;
  risk_level?: string;
  override: boolean;
  override_reason?: string;
  evidence_verdict?: string;
}

// ── Helpers ──────────────────────────────────────────────────

const PHASE_ORDER = ['PLAN', 'ACT', 'OBSERVE', 'VERIFY'] as const;

const phaseColor = (state: string): string => {
  switch (state) {
    case 'PLAN': return 'text-amber-400';
    case 'ACT': return 'text-sky-400';
    case 'OBSERVE': return 'text-emerald-400';
    case 'VERIFY': return 'text-violet-400';
    default: return 'text-gray-500';
  }
};

const phaseBorderColor = (state: string): string => {
  switch (state) {
    case 'PLAN': return 'border-amber-700';
    case 'ACT': return 'border-sky-700';
    case 'OBSERVE': return 'border-emerald-700';
    case 'VERIFY': return 'border-violet-700';
    default: return 'border-industrial-border';
  }
};

const statusConfig = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return { bg: 'bg-emerald-950/60', border: 'border-emerald-800', text: 'text-emerald-400', icon: CheckCircle2 };
    case 'FAILURE':
      return { bg: 'bg-red-950/60', border: 'border-red-800', text: 'text-red-400', icon: XCircle };
    case 'APPROVAL_REQUIRED':
      return { bg: 'bg-amber-950/60', border: 'border-amber-700', text: 'text-amber-400', icon: ShieldAlert };
    default:
      return { bg: 'bg-yellow-950/40', border: 'border-yellow-800', text: 'text-yellow-400', icon: Loader2 };
  }
};

const formatArtifactLinks = (text: string) => {
  if (!text) return null;
  const regex = /([a-zA-Z0-9_\-\.]+\.(docx|xlsx|pptx|png|jpg|csv|txt))/gi;
  const lines = text.split('\n');
  return lines.map((line, i) => {
    if (line.includes("artifacts/") || line.includes("generated at") || regex.test(line)) {
      const match = line.match(regex);
      if (match && match.length > 0) {
        const filename = match[match.length - 1];
        return (
          <div key={i} className="flex items-center gap-2 py-0.5">
            <FileDown className="w-3 h-3 text-industrial-accent shrink-0" />
            <span className="text-gray-400">{line.split(filename)[0]}</span>
            <a
              href={`http://localhost:8000/artifacts/${filename}`}
              target="_blank"
              rel="noreferrer"
              className="text-industrial-accent hover:text-amber-300 underline underline-offset-2 font-mono text-xs transition-colors"
            >
              {filename}
            </a>
          </div>
        );
      }
    }
    return <div key={i} className="py-0.5">{line}</div>;
  });
};

// ── Phase Progress Bar ───────────────────────────────────────

const PhaseIndicator: React.FC<{ currentPhase: string }> = ({ currentPhase }) => {
  const activeIndex = PHASE_ORDER.indexOf(currentPhase as any);
  return (
    <div className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest">
      {PHASE_ORDER.map((phase, i) => {
        const isActive = i === activeIndex;
        const isPast = i < activeIndex;
        return (
          <React.Fragment key={phase}>
            {i > 0 && (
              <ChevronRight className={`w-3 h-3 ${isPast ? 'text-gray-500' : 'text-gray-700'}`} />
            )}
            <span className={`px-2 py-0.5 rounded-sm transition-colors ${
              isActive ? `${phaseColor(phase)} bg-white/5 font-bold` :
              isPast ? 'text-gray-500' : 'text-gray-700'
            }`}>
              {phase}
            </span>
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ── Evidence Inspector Component ─────────────────────────────

const EvidenceBlock: React.FC<{ evidence: EvidenceRecord[] }> = ({ evidence }) => {
  const [expanded, setExpanded] = useState(true);

  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="mt-2 border border-industrial-border bg-industrial-surface/40 rounded-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-1.5 bg-industrial-base/80 border-b border-industrial-border text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5 text-industrial-accent" />
          <span className="font-mono text-[11px] font-bold text-gray-300 uppercase tracking-wider">
            Verified Citations ({evidence.length})
          </span>
        </div>
        <ChevronRight className={`w-3 h-3 text-gray-500 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {expanded && (
        <div className="p-2 space-y-2">
          {evidence.map((rec, i) => {
            const docName = rec.filename || rec.source_doc || 'Unknown Document';
            const scorePct = Math.round((rec.score || 0) * 100);
            const textContent = rec.text || rec.snippet || '';

            return (
              <div key={i} className="border border-industrial-border/60 bg-industrial-base p-2.5 rounded-sm">
                <div className="flex items-center justify-between mb-1.5 text-[11px]">
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3 h-3 text-sky-400 shrink-0" />
                    <span className="font-mono text-gray-200 font-medium truncate" title={docName}>
                      {docName}
                    </span>
                    {rec.page !== undefined && rec.page !== null && (
                      <span className="font-mono text-[10px] text-gray-500 bg-industrial-surface px-1.5 py-0.5 rounded border border-industrial-border">
                        PAGE {rec.page}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0 pl-2">
                    <span className="font-mono text-[10px] text-gray-500">RELEVANCE:</span>
                    <span className={`font-mono text-[10px] font-bold ${
                      scorePct >= 70 ? 'text-emerald-400' : scorePct >= 35 ? 'text-amber-400' : 'text-red-400'
                    }`}>
                      {scorePct}%
                    </span>
                  </div>
                </div>

                <div className="w-full bg-gray-900 h-1 rounded-full overflow-hidden mb-2">
                  <div 
                    className={`h-full ${scorePct >= 70 ? 'bg-emerald-500' : scorePct >= 35 ? 'bg-industrial-accent' : 'bg-red-500'}`} 
                    style={{ width: `${Math.min(100, Math.max(5, scorePct))}%` }}
                  />
                </div>

                <p className="text-[11px] font-mono text-gray-400 leading-relaxed bg-black/30 p-2 rounded border border-industrial-border/30 line-clamp-3 hover:line-clamp-none transition-all">
                  {textContent}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ── Tool Row ─────────────────────────────────────────────────

const ToolCallRow: React.FC<{ toolCall: any }> = ({ toolCall }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border border-industrial-border bg-industrial-base rounded-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-3 py-2 text-xs hover:bg-white/[0.02] transition-colors text-left"
      >
        <Wrench className="w-3 h-3 text-industrial-accent shrink-0" />
        <span className="font-mono text-sky-400 font-medium">{toolCall.name}</span>
        <ChevronRight className={`w-3 h-3 text-gray-600 ml-auto transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      {expanded && toolCall.args && (
        <pre className="px-3 pb-2 text-[11px] font-mono text-gray-500 overflow-x-auto leading-relaxed border-t border-industrial-border bg-black/20">
          {JSON.stringify(toolCall.args, null, 2)}
        </pre>
      )}
    </div>
  );
};

// ── Step Renderer ────────────────────────────────────────────

const StepEntry: React.FC<{ step: AgentStep; index: number }> = ({ step, index }) => {
  return (
    <div className={`relative pl-6 pb-4 border-l ${phaseBorderColor(step.state)} last:pb-0`}>
      <div className={`absolute -left-[5px] top-0 w-[9px] h-[9px] rounded-full border-2 ${phaseBorderColor(step.state)} bg-industrial-base`} />

      <div className="flex items-center gap-3 mb-1.5">
        <span className="font-mono text-[10px] text-gray-600">STEP {String(index + 1).padStart(2, '0')}</span>
        <span className={`font-mono text-[11px] font-bold tracking-wider ${phaseColor(step.state)}`}>
          {step.state}
        </span>
        {step.timestamp && (
          <span className="font-mono text-[10px] text-gray-700 ml-auto">
            {new Date(step.timestamp).toLocaleTimeString('en-US', { hour12: false })}
          </span>
        )}
      </div>

      {step.thought && (
        <p className="text-[13px] text-gray-400 leading-relaxed mb-2 pl-1 border-l-2 border-gray-800 ml-1">
          {step.thought}
        </p>
      )}

      {step.tool_call && (
        <div className="mb-2">
          <ToolCallRow toolCall={step.tool_call} />
        </div>
      )}

      {step.evidence && step.evidence.length > 0 && (
        <EvidenceBlock evidence={step.evidence} />
      )}

      {step.tool_result && (
        <div className="mt-2 bg-industrial-base border border-industrial-border rounded-sm p-2 text-[12px] font-mono text-gray-400 max-h-36 overflow-y-auto leading-relaxed">
          {formatArtifactLinks(step.tool_result)}
        </div>
      )}

      {step.error && (
        <div className="flex items-start gap-2 bg-red-950/30 border border-red-900 rounded-sm p-2 text-[12px] text-red-400 mt-2">
          <XCircle className="w-3 h-3 shrink-0 mt-0.5" />
          <span className="font-mono">{step.error}</span>
        </div>
      )}
    </div>
  );
};

// ── Main Panel ───────────────────────────────────────────────

const AgentWorkspacePanel: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [prompt, setPrompt] = useState("");
  const [currentTask, setCurrentTask] = useState<AgentTask | null>(null);
  const [loading, setLoading] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showAudit, setShowAudit] = useState(false);
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  
  // Approval Form State
  const [overrideChecked, setOverrideChecked] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const traceEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    axios.get("http://localhost:8000/agent/tools")
      .then(res => setTools(res.data))
      .catch(err => console.error("Failed to load tools", err));
  }, []);

  const loadAuditLogs = (taskId?: string) => {
    const url = taskId 
      ? `http://localhost:8000/agent/audit?task_id=${taskId}&limit=20`
      : `http://localhost:8000/agent/audit?limit=20`;
    axios.get(url)
      .then(res => setAuditLogs(res.data.entries || []))
      .catch(err => console.error("Failed to load audit logs", err));
  };

  useEffect(() => {
    if (showAudit) {
      loadAuditLogs(currentTask?.task_id);
    }
  }, [showAudit, currentTask?.task_id]);

  useEffect(() => {
    if (traceEndRef.current) {
      traceEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentTask?.steps, currentTask?.status]);

  const pollTask = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`http://localhost:8000/agent/tasks/${taskId}`);
        const task: AgentTask = res.data.task;
        setCurrentTask(task);

        if (task.status === 'SUCCESS' || task.status === 'FAILURE') {
          setLoading(false);
          clearInterval(interval);
          if (showAudit) loadAuditLogs(taskId);
        } else if (task.status === 'APPROVAL_REQUIRED') {
          setLoading(false);
          clearInterval(interval);
          if (showAudit) loadAuditLogs(taskId);
        }
      } catch (e) {
        console.error(e);
        setLoading(false);
        clearInterval(interval);
      }
    }, 1500);
  };

  const handleStartTask = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setCurrentTask(null);
    setActionError(null);
    setOverrideChecked(false);
    setOverrideReason("");
    setRejectReason("");
    setShowRejectInput(false);

    try {
      const res = await axios.post("http://localhost:8000/agent/tasks", { prompt });
      const task: AgentTask = res.data.task;
      setCurrentTask(task);
      pollTask(task.task_id);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!currentTask) return;
    setActionError(null);
    setLoading(true);

    try {
      await axios.post(`http://localhost:8000/agent/tasks/${currentTask.task_id}/approve`, {
        actor: "lead_operator",
        override: overrideChecked,
        override_reason: overrideReason
      });
      pollTask(currentTask.task_id);
    } catch (e: any) {
      setLoading(false);
      const detail = e.response?.data?.detail || e.message;
      setActionError(detail);
    }
  };

  const handleReject = async () => {
    if (!currentTask) return;
    setActionError(null);
    setLoading(true);

    try {
      const res = await axios.post(`http://localhost:8000/agent/tasks/${currentTask.task_id}/reject`, {
        actor: "lead_operator",
        reason: rejectReason || "Operator rejected proposed action."
      });
      setCurrentTask(res.data.task);
      setLoading(false);
      if (showAudit) loadAuditLogs(currentTask.task_id);
    } catch (e: any) {
      setLoading(false);
      const detail = e.response?.data?.detail || e.message;
      setActionError(detail);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleStartTask();
    }
  };

  const currentPhase = currentTask?.steps.length 
    ? currentTask.steps[currentTask.steps.length - 1].state 
    : '';

  const sc = currentTask ? statusConfig(currentTask.status) : null;
  const appReq = currentTask?.approval_request;
  const evVer = appReq?.evidence_verification;
  const requiresOverride = evVer?.verdict === 'INSUFFICIENT' || evVer?.verdict === 'MISSING';

  return (
    <div className="flex flex-col h-full font-sans">
      {/* ── Top bar: Task metadata ── */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-industrial-border bg-industrial-surface/50 shrink-0">
        <div className="flex items-center gap-4">
          <h2 className="font-display text-sm font-bold tracking-wide text-white uppercase">Execution Console</h2>
          {currentTask && <PhaseIndicator currentPhase={currentPhase} />}
        </div>
        <div className="flex items-center gap-3">
          {currentTask && (
            <>
              <span className="font-mono text-[10px] text-gray-600 hidden md:inline" title={currentTask.task_id}>
                ID: {currentTask.task_id.slice(0, 12)}…
              </span>
              {currentTask.selected_model && (
                <span className="font-mono text-[10px] text-gray-500 bg-industrial-base px-2 py-0.5 rounded-sm border border-industrial-border">
                  {currentTask.selected_model}
                </span>
              )}
              {sc && (
                <span className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded-sm border ${sc.bg} ${sc.border} ${sc.text} ${
                  currentTask.status !== 'SUCCESS' && currentTask.status !== 'FAILURE' ? 'sovra-pulse' : ''
                }`}>
                  {currentTask.status}
                </span>
              )}
            </>
          )}

          <button
            onClick={() => setShowAudit(!showAudit)}
            className={`flex items-center gap-1.5 text-[10px] font-mono uppercase px-2 py-1 rounded-sm border transition-colors ${
              showAudit 
                ? 'border-industrial-accent text-industrial-accent bg-amber-950/20' 
                : 'border-industrial-border text-gray-500 hover:text-gray-300 hover:border-gray-500'
            }`}
          >
            <History className="w-3 h-3" />
            Audit ({auditLogs.length})
          </button>

          <button
            onClick={() => setShowTools(!showTools)}
            className={`flex items-center gap-1.5 text-[10px] font-mono uppercase px-2 py-1 rounded-sm border transition-colors ${
              showTools 
                ? 'border-industrial-accent text-industrial-accent bg-amber-950/20' 
                : 'border-industrial-border text-gray-500 hover:text-gray-300 hover:border-gray-500'
            }`}
          >
            <Wrench className="w-3 h-3" />
            Tools ({tools.length})
          </button>
        </div>
      </div>

      {/* ── Tools drawer ── */}
      {showTools && (
        <div className="border-b border-industrial-border bg-industrial-base px-5 py-3 shrink-0">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-1">
            {tools.map((t, idx) => (
              <div key={idx} className="flex items-baseline gap-2 py-1 text-[11px]">
                <span className="font-mono text-industrial-accent font-medium shrink-0">{t.name}</span>
                <span className="text-gray-600 truncate">{t.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Audit log drawer ── */}
      {showAudit && (
        <div className="border-b border-industrial-border bg-industrial-base px-5 py-3 shrink-0 max-h-48 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">Immutable Audit Trail (Append-Only)</span>
            <button onClick={() => loadAuditLogs(currentTask?.task_id)} className="text-[10px] font-mono text-industrial-accent hover:underline">
              Refresh
            </button>
          </div>
          {auditLogs.length === 0 ? (
            <p className="text-xs text-gray-600 font-mono">No audit records recorded yet.</p>
          ) : (
            <div className="space-y-1.5">
              {auditLogs.map((log) => (
                <div key={log.entry_id} className="flex items-center gap-3 text-[11px] font-mono py-1 border-b border-industrial-border/30 last:border-0">
                  <span className="text-gray-600 shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                  </span>
                  <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                    log.action.includes('OVERRIDE') ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                    log.action.includes('GRANTED') ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                    log.action.includes('REJECTED') ? 'bg-red-950 text-red-400 border border-red-800' :
                    'bg-gray-900 text-gray-400'
                  }`}>
                    {log.action}
                  </span>
                  <span className="text-gray-400 truncate">
                    {log.tool_name ? `Tool: ${log.tool_name}` : `Actor: ${log.actor}`}
                    {log.override && log.override_reason ? ` (Override Reason: "${log.override_reason}")` : ''}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Main trace area ── */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!currentTask && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-gray-700 mb-4">
              <Play className="w-10 h-10 mx-auto mb-3" />
            </div>
            <p className="text-sm text-gray-500 font-mono">No active task.</p>
            <p className="text-xs text-gray-700 mt-1">Enter an instruction below to begin execution.</p>
          </div>
        )}

        {loading && !currentTask && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Loader2 className="w-6 h-6 text-industrial-accent animate-spin mb-3" />
            <p className="text-xs text-gray-500 font-mono">Initializing agent task…</p>
          </div>
        )}

        {currentTask && (
          <div className="max-w-3xl">
            <div className="mb-5 pb-3 border-b border-industrial-border">
              <span className="text-[10px] font-mono text-gray-600 uppercase tracking-wider">Task Instruction</span>
              <p className="text-sm text-gray-300 mt-1 leading-relaxed">{currentTask.prompt}</p>
            </div>

            <div className="space-y-0">
              {currentTask.steps.map((step, idx) => (
                <StepEntry key={idx} step={step} index={idx} />
              ))}
            </div>

            {loading && currentTask.status !== 'APPROVAL_REQUIRED' && (
              <div className="flex items-center gap-2 pl-6 mt-2 text-[11px] font-mono text-gray-600">
                <Loader2 className="w-3 h-3 animate-spin text-industrial-accent" />
                Processing…
              </div>
            )}

            {/* ── INDUSTRIAL HUMAN APPROVAL & EVIDENCE GATE PANEL ── */}
            {currentTask.status === 'APPROVAL_REQUIRED' && appReq && (
              <div className="mt-5 border-2 border-amber-700/80 bg-industrial-surface p-4 rounded-sm shadow-xl">
                <div className="flex items-start justify-between pb-3 border-b border-industrial-border mb-3">
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 sovra-pulse" />
                    <div>
                      <h4 className="text-sm font-display font-bold text-amber-400 uppercase tracking-wider">
                        Human Authorization Gate Required
                      </h4>
                      <p className="text-[11px] text-gray-500 font-mono">
                        SOVRA halted execution. Operator authorization is mandatory before proceeding.
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-[10px] bg-red-950/80 text-red-400 border border-red-800 px-2 py-0.5 rounded uppercase font-bold">
                      Risk: {appReq.risk_level}
                    </span>
                    <div className="flex items-center gap-1 text-[10px] font-mono text-gray-500 mt-1">
                      <Clock className="w-3 h-3 text-gray-500" />
                      Expires in 30m
                    </div>
                  </div>
                </div>

                {/* Requested Action Details */}
                <div className="bg-industrial-base p-3 rounded border border-industrial-border mb-3">
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="text-gray-400 uppercase">Target Operation:</span>
                    <span className="text-industrial-accent font-bold">{appReq.tool_name}</span>
                  </div>
                  <div className="text-[11px] font-mono text-gray-500">
                    <span className="text-gray-400">Parameters: </span>
                    <code className="text-gray-300">{JSON.stringify(appReq.tool_args)}</code>
                  </div>
                </div>

                {/* Evidence Gate Evaluation */}
                {evVer && (
                  <div className="bg-industrial-base p-3 rounded border border-industrial-border mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <KeyRound className="w-3.5 h-3.5 text-industrial-accent" />
                        <span className="text-xs font-mono font-bold text-gray-300 uppercase">Evidence Gate Verification</span>
                      </div>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                        evVer.verdict === 'SUFFICIENT' ? 'bg-emerald-950 text-emerald-400 border-emerald-800' :
                        evVer.verdict === 'INSUFFICIENT' ? 'bg-amber-950 text-amber-400 border-amber-800' :
                        'bg-red-950 text-red-400 border-red-800'
                      }`}>
                        Verdict: {evVer.verdict}
                      </span>
                    </div>

                    <p className="text-[11px] font-mono text-gray-400 mb-2 leading-relaxed">
                      {evVer.details}
                    </p>

                    <div className="flex items-center gap-4 text-[10px] font-mono text-gray-500 border-t border-industrial-border/40 pt-2">
                      <span>PEAK SCORE: <strong className="text-gray-300">{evVer.max_score}</strong></span>
                      <span>EVALUATED AT: <strong className="text-gray-300">{new Date(evVer.evaluated_at || Date.now()).toLocaleTimeString()}</strong></span>
                      <span>OVERRIDE REQUIRED: <strong className={requiresOverride ? 'text-amber-400' : 'text-gray-300'}>{requiresOverride ? 'YES' : 'NO'}</strong></span>
                    </div>
                  </div>
                )}

                {/* Insufficient Evidence Warning & Override Controls */}
                {requiresOverride && (
                  <div className="bg-amber-950/30 border border-amber-700/60 p-3 rounded mb-4">
                    <div className="flex items-center gap-2 text-amber-400 text-xs font-mono font-bold mb-1">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      INSUFFICIENT EVIDENCE WARNING (POLICY LOCK)
                    </div>
                    <p className="text-[11px] text-gray-400 font-mono mb-3 leading-relaxed">
                      This sensitive action lacks sufficient verified citations. In compliance with safety standards, approval cannot proceed without explicit operator override and written justification.
                    </p>

                    <label className="flex items-center gap-2 cursor-pointer mb-2">
                      <input 
                        type="checkbox" 
                        checked={overrideChecked}
                        onChange={(e) => setOverrideChecked(e.target.checked)}
                        className="rounded border-gray-700 text-amber-600 focus:ring-amber-500"
                      />
                      <span className="text-xs font-mono text-gray-200 font-medium">
                        I explicitly authorize override for this insufficient evidence action
                      </span>
                    </label>

                    {overrideChecked && (
                      <div className="mt-2">
                        <label className="block text-[10px] font-mono text-gray-400 uppercase mb-1">
                          Override Justification Reason (Mandatory for Audit Trail):
                        </label>
                        <input 
                          type="text"
                          value={overrideReason}
                          onChange={(e) => setOverrideReason(e.target.value)}
                          placeholder="e.g., Physical calibration verified on-site by Plant Engineer"
                          className="w-full bg-industrial-base border border-amber-700 rounded px-2.5 py-1.5 text-xs text-gray-200 font-mono focus:border-amber-400"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Error Banner */}
                {actionError && (
                  <div className="bg-red-950/40 border border-red-800 text-red-400 text-xs font-mono p-2.5 rounded mb-3">
                    {actionError}
                  </div>
                )}

                {/* Reject Input */}
                {showRejectInput && (
                  <div className="bg-red-950/20 border border-red-800/60 p-3 rounded mb-3">
                    <label className="block text-[10px] font-mono text-red-400 uppercase mb-1">
                      Rejection Reason (Recorded to Audit Trail):
                    </label>
                    <input 
                      type="text"
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="e.g., Unverified pump parameters, request manual inspection"
                      className="w-full bg-industrial-base border border-red-800 rounded px-2.5 py-1.5 text-xs text-gray-200 font-mono"
                    />
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center gap-3 pt-2">
                  <button
                    disabled={loading || (requiresOverride && (!overrideChecked || !overrideReason.trim()))}
                    onClick={handleApprove}
                    className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-mono font-bold uppercase tracking-wider transition-colors ${
                      loading || (requiresOverride && (!overrideChecked || !overrideReason.trim()))
                        ? 'bg-gray-800 text-gray-600 cursor-not-allowed border border-gray-700'
                        : 'bg-amber-600 hover:bg-amber-500 text-black border border-amber-500'
                    }`}
                  >
                    <ShieldCheck className="w-4 h-4" />
                    Authorize Execution
                  </button>

                  {!showRejectInput ? (
                    <button
                      disabled={loading}
                      onClick={() => setShowRejectInput(true)}
                      className="flex items-center gap-1.5 px-3 py-2 rounded text-xs font-mono text-red-400 hover:text-red-300 hover:bg-red-950/30 border border-red-900/60 transition-colors"
                    >
                      <ShieldX className="w-3.5 h-3.5" />
                      Reject Action…
                    </button>
                  ) : (
                    <button
                      disabled={loading}
                      onClick={handleReject}
                      className="flex items-center gap-1.5 px-4 py-2 rounded text-xs font-mono font-bold uppercase tracking-wider bg-red-900 hover:bg-red-800 text-white border border-red-700 transition-colors"
                    >
                      Confirm Rejection
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Final result */}
            {currentTask.final_result && (
              <div className="mt-4 border border-emerald-900 bg-emerald-950/20 p-4 rounded-sm">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-display font-bold text-emerald-400 uppercase tracking-wide">
                    Execution Complete
                  </span>
                </div>
                <div className="text-[13px] text-gray-300 whitespace-pre-wrap leading-relaxed font-sans">
                  {formatArtifactLinks(currentTask.final_result)}
                </div>
              </div>
            )}

            {/* Failure result */}
            {currentTask.status === 'FAILURE' && (
              <div className="mt-4 border border-red-900 bg-red-950/20 p-4 rounded-sm">
                <div className="flex items-center gap-2 mb-1">
                  <XCircle className="w-4 h-4 text-red-500" />
                  <span className="text-xs font-display font-bold text-red-400 uppercase tracking-wide">
                    Execution Terminated
                  </span>
                </div>
                <p className="text-xs font-mono text-red-300 mt-1">
                  {currentTask.final_result || "The task failed or was terminated by human rejection."}
                </p>
              </div>
            )}

            <div ref={traceEndRef} />
          </div>
        )}
      </div>

      {/* ── Demo Preset Workflows Bar ── */}
      <div className="shrink-0 border-t border-industrial-border bg-black/40 px-5 py-2">
        <div className="flex items-center gap-2 overflow-x-auto text-[11px] font-mono">
          <span className="text-gray-500 uppercase tracking-wider shrink-0 text-[10px]">Phase 7 Demo:</span>
          <button
            type="button"
            onClick={() => setPrompt("Review Centrifugal Slurry Pump P-104A inspection findings: Vibration is 5.2 mm/s, bearing temperature is 82C, seal leakage is 14 drops/min. Query the SOP in our knowledge base for threshold limits, compare findings, evaluate via Evidence Gate, and generate a formal inspection recommendation DOCX report named pump_audit_report.docx.")}
            className="px-2.5 py-1 rounded bg-industrial-surface border border-industrial-border text-gray-300 hover:border-industrial-accent hover:text-industrial-accent transition-colors shrink-0"
          >
            WF-1: Pump SOP & DOCX
          </button>
          <button
            type="button"
            onClick={() => setPrompt("Analyze the engineering P&ID drawing data/pid_cooling_loop.png. Extract all visible valve tags, pump identifiers, and instrumentation loops. Cross-reference operating vibration and temperature limits against our knowledge base SOP.")}
            className="px-2.5 py-1 rounded bg-industrial-surface border border-industrial-border text-gray-300 hover:border-industrial-accent hover:text-industrial-accent transition-colors shrink-0"
          >
            WF-2: P&ID Drawing Inspection
          </button>
          <button
            type="button"
            onClick={() => setPrompt("Audit the vibration telemetry dataset data/vibration_telemetry.csv using deterministic tabular calculation. Calculate exact RMS vibration mean and peak, audit threshold exceedances (> 4.5 mm/s), and generate an Excel audit report named telemetry_audit.xlsx.")}
            className="px-2.5 py-1 rounded bg-industrial-surface border border-industrial-border text-gray-300 hover:border-industrial-accent hover:text-industrial-accent transition-colors shrink-0"
          >
            WF-3: Telemetry CSV & XLSX
          </button>
          <span className="ml-auto text-[10px] text-amber-500/80 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-800/40 shrink-0">
            SYNTHETIC DEMO ASSETS
          </span>
        </div>
      </div>

      {/* ── Input bar (pinned bottom) ── */}
      <div className="shrink-0 border-t border-industrial-border bg-industrial-surface/50 px-5 py-3">
        <div className="flex items-end gap-3 max-w-3xl">
          <textarea
            className="flex-1 bg-industrial-base border border-industrial-border rounded-sm px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 font-sans resize-none focus:border-industrial-accent transition-colors leading-relaxed"
            rows={2}
            placeholder="Enter task instruction…"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className={`flex items-center gap-2 px-5 py-2.5 rounded-sm text-xs font-mono font-bold uppercase tracking-wider transition-all shrink-0 ${
              loading
                ? 'bg-gray-800 text-gray-600 cursor-not-allowed border border-gray-700'
                : 'bg-industrial-accent hover:bg-industrial-accent-hover text-black border border-industrial-accent'
            }`}
            onClick={handleStartTask}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Running
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                Execute
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentWorkspacePanel;
