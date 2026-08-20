import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { getApiKeyStatus, saveApiKey } from "../api/client";

type KeyState = "loading" | "saved" | "not_saved" | "changing";

export function SettingsPage() {
  const navigate = useNavigate();
  const [keyState, setKeyState] = useState<KeyState>("loading");
  const [keyHint, setKeyHint] = useState("");
  const [newKey, setNewKey] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadKeyStatus();
  }, []);

  const loadKeyStatus = async () => {
    try {
      const status = await getApiKeyStatus();
      setKeyHint(status.keyHint);
      setKeyState(status.hasKey ? "saved" : "not_saved");
    } catch {
      setKeyState("not_saved");
    }
  };

  const handleSave = async () => {
    if (!newKey.trim()) {
      toast.error("Please enter an API key");
      return;
    }
    setSaving(true);
    try {
      await saveApiKey(newKey.trim());
      toast.success("API key saved securely");
      setNewKey("");
      await loadKeyStatus();
      setKeyState("saved");
    } catch {
      toast.error("Failed to save API key");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">

      {/* Back button */}
      <button
        onClick={() => navigate("/dashboard")}
        className="flex items-center gap-2 text-gray-400
                   hover:text-white mb-8 transition-colors"
      >
        ← Back to Dashboard
      </button>

      <h1 className="text-2xl font-bold mb-1">Settings</h1>
      <p className="text-gray-400 mb-8">
        Manage your profile and AI provider settings
      </p>

      {/* Gemini API Key Card */}
      <div className="bg-gray-900 border border-gray-700 rounded-xl
                      p-6 max-w-2xl mb-6">

        <div className="flex items-center gap-3 mb-1">
          <span className="text-xl">🔑</span>
          <h2 className="text-lg font-semibold">Gemini API Key</h2>
        </div>

        <p className="text-gray-400 text-sm mb-5">
          UnitForge uses your key for AI test generation — your quota,
          your data relationship with Google.
          Stored encrypted with AES-256, never shown in full.
          Get one free at{" "}
          <a
            href="https://aistudio.google.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:underline"
          >
            aistudio.google.com
          </a>
        </p>

        {/* Loading state */}
        {keyState === "loading" && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <span className="animate-spin">⟳</span>
            Checking key status...
          </div>
        )}

        {/* Key is saved — show confirmation */}
        {keyState === "saved" && (
          <div>
            <div className="flex items-center gap-3 p-4 bg-green-900
                            bg-opacity-30 border border-green-700
                            rounded-lg mb-4">
              <span className="text-green-400 text-xl">✓</span>
              <div>
                <p className="text-green-300 font-medium text-sm">
                  API key is saved and active
                </p>
                <p className="text-green-500 text-xs mt-0.5 font-mono">
                  •••••••••••••••••••••••••••••••{keyHint}
                </p>
              </div>
            </div>
            <button
              onClick={() => setKeyState("changing")}
              className="px-4 py-2 border border-gray-600 rounded-lg
                         text-gray-300 hover:text-white hover:border-gray-400
                         text-sm transition-colors"
            >
              Change API Key
            </button>
          </div>
        )}

        {/* No key saved */}
        {keyState === "not_saved" && (
          <div>
            <div className="flex items-center gap-3 p-4 bg-yellow-900
                            bg-opacity-30 border border-yellow-700
                            rounded-lg mb-4">
              <span className="text-yellow-400 text-xl">⚠</span>
              <div>
                <p className="text-yellow-300 font-medium text-sm">
                  No API key saved
                </p>
                <p className="text-yellow-500 text-xs mt-0.5">
                  Add your Gemini API key to start generating tests
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <input
                type="password"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                placeholder="Paste your Gemini API key"
                className="flex-1 px-4 py-3 bg-gray-800 border
                           border-gray-600 rounded-lg text-white
                           placeholder-gray-500 focus:outline-none
                           focus:border-indigo-500"
              />
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700
                           rounded-lg text-white font-medium
                           transition-colors disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        )}

        {/* Changing key */}
        {keyState === "changing" && (
          <div>
            <p className="text-gray-300 text-sm mb-3">
              Enter your new Gemini API key.
              This will replace the current key.
            </p>
            <div className="flex gap-3 mb-3">
              <input
                type="password"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                placeholder="Paste new Gemini API key"
                className="flex-1 px-4 py-3 bg-gray-800 border
                           border-gray-600 rounded-lg text-white
                           placeholder-gray-500 focus:outline-none
                           focus:border-indigo-500"
              />
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700
                           rounded-lg text-white font-medium
                           transition-colors disabled:opacity-50"
              >
                {saving ? "Saving..." : "Update"}
              </button>
            </div>
            <button
              onClick={() => {
                setNewKey("");
                setKeyState("saved");
              }}
              className="text-gray-400 hover:text-white text-sm
                         transition-colors"
            >
              Cancel — keep current key
            </button>
          </div>
        )}

        <p className="text-xs text-gray-600 mt-4">
          Your key is encrypted with AES-256 before storage.
          UnitForge only uses it for your test generation requests.
          It is never logged or shared.
        </p>
      </div>

      {/* Footer */}
      <p className="text-xs text-gray-600 max-w-2xl">
        UnitForge is open source · MIT license ·
        your data stays in your account and your AI key stays yours
      </p>
    </div>
  );
}
