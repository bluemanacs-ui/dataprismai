type SidebarProps = {
  activeView: "chat" | "explorer";
  onChangeView: (view: "chat" | "explorer") => void;
};

const chats = [
  "Revenue trend by region",
  "Margin analysis Q2",
  "Top churn drivers",
];

const navItems = [
  "Saved Reports",
  "Metrics",
  "Datasets",
  "Skills",
  "Admin",
];

export function Sidebar({ activeView, onChangeView }: SidebarProps) {
  return (
    <aside className="hidden w-72 border-r border-zinc-800 bg-zinc-950 lg:flex lg:flex-col">
      <div className="p-4">
        <button
          onClick={() => onChangeView("chat")}
          className="w-full rounded-xl bg-blue-600 px-4 py-3 text-left text-sm font-medium text-white hover:bg-blue-500"
        >
          + New Chat
        </button>
      </div>

      <div className="px-4">
        <input
          placeholder="Search chats or metrics..."
          className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 outline-none placeholder:text-zinc-500"
        />
      </div>

      <div className="mt-4 px-4">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Workspace
        </div>
        <div className="space-y-2">
          <button
            onClick={() => onChangeView("chat")}
            className={`w-full rounded-xl px-3 py-2 text-left text-sm ${
              activeView === "chat"
                ? "bg-zinc-900 text-zinc-100"
                : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => onChangeView("explorer")}
            className={`w-full rounded-xl px-3 py-2 text-left text-sm ${
              activeView === "explorer"
                ? "bg-zinc-900 text-zinc-100"
                : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
            }`}
          >
            Data Explorer
          </button>
        </div>
      </div>

      <div className="mt-6 px-4">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Recent Chats
        </div>
        <div className="space-y-2">
          {chats.map((chat) => (
            <button
              key={chat}
              onClick={() => onChangeView("chat")}
              className="w-full rounded-xl px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-900"
            >
              {chat}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 border-t border-zinc-800 px-4 pt-4">
        <div className="space-y-2">
          {navItems.map((item) => (
            <button
              key={item}
              className="w-full rounded-xl px-3 py-2 text-left text-sm text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
            >
              {item}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
