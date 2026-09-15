import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface AgentStep {
  step_id: string;
  state: string;
  timestamp: string;
  thought?: string;
  tool_call?: any;
  tool_result?: string;
  error?: string;
}

interface AgentTask {
  task_id: string;
  prompt: string;
  status: string;
  steps: AgentStep[];
  final_result?: string;
  selected_model?: string;
}

interface Tool {
  name: string;
  description: string;
}

const AgentWorkspacePanel: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [prompt, setPrompt] = useState("");
  const [currentTask, setCurrentTask] = useState<AgentTask | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch available tools
    axios.get("http://localhost:8000/agent/tools")
      .then(res => setTools(res.data))
      .catch(err => console.error("Failed to load tools", err));
  }, []);

  const pollTask = async (taskId: string) => {
    try {
      const res = await axios.get(`http://localhost:8000/agent/tasks/${taskId}`);
      const task = res.data.task;
      setCurrentTask(task);
      
      if (task.status !== 'SUCCESS' && task.status !== 'FAILURE') {
        setTimeout(() => pollTask(taskId), 2000);
      } else {
        setLoading(false);
      }
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const handleStartTask = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setCurrentTask(null);
    try {
      const res = await axios.post("http://localhost:8000/agent/tasks", { prompt });
      const task = res.data.task;
      setCurrentTask(task);
      pollTask(task.task_id);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#121212] border border-[#333] rounded-lg p-6 font-mono text-[#E0E0E0]">
      <h2 className="text-xl font-bold text-orange-400 mb-4 tracking-wider">SOVRA AGENT WORKSPACE</h2>
      
      <div className="mb-6 bg-[#1a1a1a] p-4 rounded border border-[#2a2a2a]">
        <h3 className="text-sm font-semibold text-gray-400 mb-2">AVAILABLE TOOLS</h3>
        <ul className="text-xs space-y-1">
          {tools.map((t, idx) => (
            <li key={idx}><span className="text-orange-300">{t.name}</span>: {t.description}</li>
          ))}
        </ul>
      </div>

      <div className="mb-6 flex space-x-4">
        <textarea 
          className="flex-1 bg-[#1a1a1a] border border-[#333] rounded p-3 text-sm focus:outline-none focus:border-orange-500 transition-colors"
          rows={3}
          placeholder="Enter task instructions..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button 
          className={`px-6 py-3 rounded font-bold text-sm tracking-wider transition-all
            ${loading ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-orange-600 hover:bg-orange-500 text-white'}`}
          onClick={handleStartTask}
          disabled={loading}
        >
          {loading ? 'EXECUTING...' : 'START TASK'}
        </button>
      </div>

      {currentTask && (
        <div className="bg-[#0a0a0a] border border-[#222] rounded p-4">
          <div className="flex justify-between items-center border-b border-[#222] pb-2 mb-4">
            <span className="text-xs text-gray-500">TASK: {currentTask.task_id}</span>
            <div className="flex items-center space-x-3">
              <span className="text-xs bg-[#222] px-2 py-1 rounded">MODEL: {currentTask.selected_model || 'PENDING'}</span>
              <span className={`text-xs px-2 py-1 rounded font-bold
                ${currentTask.status === 'SUCCESS' ? 'bg-green-900 text-green-300' : 
                  currentTask.status === 'FAILURE' ? 'bg-red-900 text-red-300' : 
                  'bg-yellow-900 text-yellow-300 animate-pulse'}`}>
                {currentTask.status}
              </span>
            </div>
          </div>

          <div className="space-y-4 max-h-[500px] overflow-y-auto">
            {currentTask.steps.map((step, idx) => (
              <div key={idx} className="border-l-2 border-[#333] pl-4 py-1">
                <div className="text-xs text-gray-500 mb-1">
                  STEP {idx + 1} <span className="text-orange-400">[{step.state}]</span>
                </div>
                {step.thought && <div className="text-sm text-gray-300 italic mb-2">"{step.thought}"</div>}
                
                {step.tool_call && (
                  <div className="bg-[#111] p-2 rounded border border-[#222] mb-2 text-xs text-blue-300">
                    <div><span className="font-bold">EXEC:</span> {step.tool_call.name}</div>
                    <pre className="mt-1 text-gray-400">{JSON.stringify(step.tool_call.args, null, 2)}</pre>
                  </div>
                )}

                {step.tool_result && (
                  <div className="bg-[#111] p-2 rounded border border-[#222] text-xs text-green-400 max-h-40 overflow-y-auto">
                    {step.tool_result}
                  </div>
                )}

                {step.error && (
                  <div className="text-xs text-red-400 mt-2">
                    ERROR: {step.error}
                  </div>
                )}
              </div>
            ))}
            
            {currentTask.final_result && (
              <div className="mt-6 border border-green-800 bg-green-900/20 p-4 rounded">
                <h4 className="text-green-500 font-bold text-sm mb-2">FINAL RESULT</h4>
                <div className="text-sm text-gray-200 whitespace-pre-wrap">{currentTask.final_result}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentWorkspacePanel;
