export function TopBar() {
  return (
    <header className="flex h-14 items-center justify-between border-b border-zinc-800 px-4">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-blue-600 px-2 py-1 text-xs font-semibold text-white">
          DataPrismAI
        </div>
        <div className="hidden text-sm text-zinc-400 md:block">
          Enterprise GenBI Insight Copilot
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <select className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-zinc-200">
          <option>Workspace: Default</option>
        </select>

        <select className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-zinc-200">
          <option>Persona: Analyst</option>
          <option>Persona: CFO</option>
          <option>Persona: Manager</option>
          <option>Persona: Product</option>
          <option>Persona: Engineer</option>
        </select>

        <select className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-zinc-200">
          <option>Model: Local</option>
        </select>
      </div>
    </header>
  );
}
