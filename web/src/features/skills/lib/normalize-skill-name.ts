/**
 * Converts a kebab-case skill name to a human-readable title.
 * e.g. "data-analysis" → "Data Analysis", "web-research" → "Web Research"
 */
export function normalizeSkillName(name: string): string {
  return name
    .split(/[-_]+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
