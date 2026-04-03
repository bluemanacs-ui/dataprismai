"use client";

import { useMemo, useState } from "react";
import { SkillCatalogResponse } from "@/types/chat";

type SkillsPanelProps = {
    catalog?: SkillCatalogResponse | null;
};

function statusClasses(status: string) {
    const value = status.toLowerCase();
    if (value === "active") return "bg-emerald-950 text-emerald-300 border-emerald-800";
    if (value === "beta") return "bg-amber-950 text-amber-300 border-amber-800";
    return "bg-zinc-900 text-zinc-300 border-zinc-700";
}

export function SkillsPanel({ catalog }: SkillsPanelProps) {
    const [query, setQuery] = useState("");

    const filteredSkills = useMemo(() => {
        if (!catalog?.skills) return [];
        const q = query.trim().toLowerCase();
        if (!q) return catalog.skills;

        return catalog.skills.filter((skill) => {
            return (
                skill.name.toLowerCase().includes(q) ||
                skill.title.toLowerCase().includes(q) ||
                skill.owner.toLowerCase().includes(q) ||
                skill.description.toLowerCase().includes(q) ||
                skill.scope.some((s) => s.toLowerCase().includes(q))
            );
        });
    }, [catalog, query]);

    return (
        <div className="space-y-4">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="mb-3 text-lg font-semibold">Skill Marketplace</div>
                <div className="mb-2 text-sm text-zinc-400">
                    BMAD-governed skills powering DataPrismAI capabilities.
                </div>
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search skills, owners, scopes..."
                    className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
                />
            </div>

            <div className="grid gap-4">
                {filteredSkills.map((skill) => (
                    <div
                        key={skill.name}
                        className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4"
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <div className="text-base font-semibold">{skill.title}</div>
                                <div className="mt-1 text-xs text-zinc-500">
                                    {skill.name} · v{skill.version} · Owner: {skill.owner}
                                </div>
                            </div>
                            <div
                                className={`rounded-full border px-3 py-1 text-xs ${statusClasses(
                                    skill.status
                                )}`}
                            >
                                {skill.status}
                            </div>
                        </div>

                        <div className="mt-3 text-sm text-zinc-300">{skill.description}</div>

                        <div className="mt-4">
                            <div className="mb-2 text-xs font-medium text-zinc-500">Scope</div>
                            <div className="flex flex-wrap gap-2">
                                {skill.scope.map((item) => (
                                    <span
                                        key={item}
                                        className="rounded-full bg-zinc-950 px-3 py-1 text-xs text-zinc-300"
                                    >
                                        {item}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="mt-4">
                            <div className="mb-2 text-xs font-medium text-zinc-500">
                                Guardrails
                            </div>
                            <ul className="space-y-1 text-sm text-zinc-300">
                                {skill.guardrails.map((rule) => (
                                    <li key={rule}>• {rule}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                ))}

                {!filteredSkills.length && (
                    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-500">
                        No matching skills found.
                    </div>
                )}
            </div>
        </div>
    );
}
