// Thin wrapper over Phosphor icons, keyed by a stable `name` so call sites stay decoupled.
import {
  MagnifyingGlass, Scales, ChatCircleDots, Lightning, CaretRight, ArrowRight,
  Warning, Question, Trophy, Cpu, Sparkle, Globe, PaperPlaneRight, SoccerBall,
  Target, Info, type IconProps as PhosphorProps, type Icon as PhosphorIcon,
} from "@phosphor-icons/react";

const MAP = {
  search: MagnifyingGlass,
  radar: Target,
  scale: Scales,
  chat: ChatCircleDots,
  bolt: Lightning,
  chevronRight: CaretRight,
  arrowRight: ArrowRight,
  alert: Warning,
  help: Question,
  trophy: Trophy,
  cpu: Cpu,
  sparkle: Sparkle,
  globe: Globe,
  send: PaperPlaneRight,
  ball: SoccerBall,
  info: Info,
} satisfies Record<string, PhosphorIcon>;

export type IconName = keyof typeof MAP;

export default function Icon({
  name, size = 18, weight = "regular", ...props
}: { name: IconName; size?: number } & PhosphorProps) {
  const Cmp = MAP[name];
  return <Cmp size={size} weight={weight} aria-hidden {...props} />;
}
