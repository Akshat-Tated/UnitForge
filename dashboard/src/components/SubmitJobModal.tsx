import { useState } from "react";
import toast from "react-hot-toast";
import { analyzeUrl, submitJob } from "../api/client";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onJobCreated: (jobId: string) => void;
}

type Step = "input" | "analyzing" | "submitting" | "done";

export function SubmitJobModal({ isOpen, onClose, onJobCreated }: Props) {
  const [url, setUrl] = useState("");
  const [inputType, setInputType] = useState<"python" | "openapi">("python");
  const [step, setStep] = useState<Step>("input");
  const [moduleCount, setModuleCount] = useState(0);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (!url.trim()) {
      setError("Please enter a GitHub URL");
      return;
    }
    if (!url.includes("github.com")) {
      setError("Please enter a valid GitHub URL");
      return;
    }
    setError("");
    setStep("analyzing");

    try {
      // Step 1: Analyze the URL
      const analysis = await analyzeUrl(url.trim(), inputType);
      setModuleCount(analysis.module_count);

      if (analysis.module_count === 0) {
        setError("No Python modules found in this repository");
        setStep("input");
        return;
      }

      // Step 2: Submit as a job
      setStep("submitting");
      const job = await submitJob(inputType, url.trim(), analysis.module_map);

      setStep("done");
      toast.success(`Job created! Processing ${analysis.module_count} modules`);
      onJobCreated(job.id);

      // Reset and close after short delay
      setTimeout(() => {
        setStep("input");
        setUrl("");
        onClose();
      }, 1500);

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
      setStep("input");
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center
                    justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-8
                      w-full max-w-lg mx-4">

        <h2 className="text-xl font-semibold text-white mb-2">
          Generate Tests
        </h2>
        <p className="text-gray-400 text-sm mb-6">
          Paste a GitHub URL to automatically generate unit tests
        </p>

        {/* URL Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            GitHub Repository URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/username/repository"
            disabled={step !== "input"}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-600
                       rounded-lg text-white placeholder-gray-500
                       focus:outline-none focus:border-indigo-500
                       disabled:opacity-50"
          />
        </div>

        {/* Type selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Type
          </label>
          <div className="flex gap-3">
            {(["python", "openapi"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setInputType(t)}
                disabled={step !== "input"}
                className={`flex-1 py-2 rounded-lg text-sm font-medium
                           border transition-colors disabled:opacity-50
                           ${inputType === t
                    ? "bg-indigo-600 border-indigo-600 text-white"
                    : "bg-transparent border-gray-600 text-gray-400 hover:border-gray-400"
                  }`}
              >
                {t === "python" ? "🐍 Python" : "📄 OpenAPI"}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-900 bg-opacity-40 border
                          border-red-700 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Status messages */}
        {step === "analyzing" && (
          <div className="mb-4 p-3 bg-blue-900 bg-opacity-40 border
                          border-blue-700 rounded-lg text-blue-300 text-sm
                          flex items-center gap-2">
            <span className="animate-spin inline-block">⟳</span>
            Cloning repository and analyzing code...
          </div>
        )}
        {step === "submitting" && (
          <div className="mb-4 p-3 bg-blue-900 bg-opacity-40 border
                          border-blue-700 rounded-lg text-blue-300 text-sm
                          flex items-center gap-2">
            <span className="animate-spin inline-block">⟳</span>
            Found {moduleCount} module(s) — submitting job...
          </div>
        )}
        {step === "done" && (
          <div className="mb-4 p-3 bg-green-900 bg-opacity-40 border
                          border-green-700 rounded-lg text-green-300 text-sm">
            ✓ Job created — {moduleCount} modules queued for test generation
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={step === "analyzing" || step === "submitting"}
            className="flex-1 py-3 border border-gray-600 rounded-lg
                       text-gray-400 hover:text-white hover:border-gray-400
                       transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={step !== "input"}
            className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700
                       rounded-lg text-white font-medium transition-colors
                       disabled:opacity-50"
          >
            {step === "input" ? "Generate Tests" : "Processing..."}
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-4 text-center">
          Make sure the test agent is running to process your job
        </p>
      </div>
    </div>
  );
}
