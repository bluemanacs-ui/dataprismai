export function PromptInput() {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-3">
      <div className="flex items-end gap-3">
        <textarea
          rows={3}
          placeholder="Ask anything about your data..."
          className="min-h-[72px] flex-1 resize-none bg-transparent px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
        />
        <button className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500">
          Send
        </button>
      </div>
    </div>
  );
}
