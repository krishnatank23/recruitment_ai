import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import HomePage from './pages/HomePage';
import RecruiterPage from './pages/RecruiterPage';
import CandidatePage from './pages/CandidatePage';

export default function App() {
    return (
        <div className="app-shell">
            <Sidebar />
            <div className="app-main">
                <TopBar />
                <main className="app-content">
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/recruiter" element={<RecruiterPage />} />
                        <Route path="/candidate" element={<CandidatePage />} />
                    </Routes>
                </main>
            </div>
        </div>
    );
}
