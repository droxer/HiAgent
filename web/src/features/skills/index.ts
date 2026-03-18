export { SkillsPage } from "./components/SkillsPage";
export { SkillCard } from "./components/SkillCard";
export { SkillSelector } from "./components/SkillSelector";
export { normalizeSkillName } from "./lib/normalize-skill-name";
export type { Skill, SkillInstallParams } from "./api/skills-api";
export {
  fetchSkills,
  fetchSkillDetail,
  installSkill,
  uninstallSkill,
  searchRegistry,
} from "./api/skills-api";
