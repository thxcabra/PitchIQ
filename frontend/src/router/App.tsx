import { NavLink, Route, Routes } from "react-router-dom";
import SearchPage from "../pages/SearchPage";
import ProfilePage from "../pages/ProfilePage";
import ComparePage from "../pages/ComparePage";
import ChatPage from "../pages/ChatPage";
import TeamPage from "../pages/TeamPage";
import CompetitionPage from "../pages/CompetitionPage";
import Icon, { type IconName } from "../components/Icon";

const NAV: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: "/", label: "Search", icon: "search", end: true },
  { to: "/compare", label: "Compare", icon: "scale" },
  { to: "/chat", label: "Ask PitchIQ", icon: "chat" },
];

function Nav() {
  const link = ({ isActive }: { isActive: boolean }) =>
    `inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
      isActive ? "bg-pitch-accent/15 text-pitch-accent" : "text-pitch-sub hover:text-white hover:bg-pitch-card2"
    }`;
  return (
    <header className="border-b border-pitch-line sticky top-0 z-20 bg-pitch-bg/80 backdrop-blur-lg">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-1">
        <NavLink to="/" className="flex items-center gap-2 mr-3 group" aria-label="PitchIQ home">
          <span className="grid place-items-center w-8 h-8 rounded-lg bg-pitch-accent/15 text-pitch-accent
                           ring-1 ring-pitch-accent/25 group-hover:bg-pitch-accent/25 transition-colors">
            <Icon name="ball" size={19} />
          </span>
          <span className="font-bold text-white tracking-tight text-[17px]">
            Pitch<span className="text-pitch-accent">IQ</span>
          </span>
        </NavLink>
        <nav className="flex items-center gap-1">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className={link}>
              <Icon name={n.icon} size={16} /> <span className="hidden sm:inline">{n.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/player/:id" element={<ProfilePage />} />
          <Route path="/team/:id" element={<TeamPage />} />
          <Route path="/competition/:name" element={<CompetitionPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}
