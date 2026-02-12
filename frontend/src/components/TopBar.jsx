import { useLocation } from 'react-router-dom';
import { Search, Bell, ChevronRight } from 'lucide-react';
import './TopBar.css';

const ROUTE_LABELS = {
    '/': 'Dashboard',
    '/recruiter': 'JD Generator',
    '/candidate': 'Candidates',
};

export default function TopBar() {
    const location = useLocation();
    const pageLabel = ROUTE_LABELS[location.pathname] || 'Page';

    return (
        <header className="topbar">
            <div className="topbar-left">
                <div className="topbar-breadcrumb">
                    <span className="breadcrumb-root">WOGOM</span>
                    <ChevronRight size={14} className="breadcrumb-sep" />
                    <span className="breadcrumb-current">{pageLabel}</span>
                </div>
            </div>

            <div className="topbar-right">
                <div className="topbar-search">
                    <Search size={16} className="topbar-search-icon" />
                    <input
                        type="text"
                        placeholder="Search..."
                        className="topbar-search-input"
                    />
                </div>

                <button className="topbar-icon-btn" aria-label="Notifications">
                    <Bell size={18} />
                    <span className="topbar-notif-dot" />
                </button>

                <div className="topbar-avatar">
                    <span className="avatar-initials">YT</span>
                </div>
            </div>
        </header>
    );
}
