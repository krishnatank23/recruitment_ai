import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    FileText,
    Users,
    ChevronLeft,
    ChevronRight,
    BriefcaseBusiness,
    Settings,
    HelpCircle,
} from 'lucide-react';
import { useState } from 'react';
import './Sidebar.css';

const NAV_ITEMS = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/recruiter', label: 'JD Generator', icon: FileText },
    { to: '/candidate', label: 'Candidates', icon: Users },
];

const BOTTOM_ITEMS = [
    { to: '#', label: 'Settings', icon: Settings },
    { to: '#', label: 'Help', icon: HelpCircle },
];

export default function Sidebar() {
    const location = useLocation();
    const [collapsed, setCollapsed] = useState(false);

    return (
        <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
            {/* Logo */}
            <div className="sidebar-logo">
                <BriefcaseBusiness size={28} className="sidebar-logo-icon" />
                {!collapsed && <span className="sidebar-logo-text">WOGOM</span>}
            </div>

            {/* Main Nav */}
            <nav className="sidebar-nav">
                <div className="sidebar-section-label">{!collapsed && 'MAIN MENU'}</div>
                {NAV_ITEMS.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.to;
                    return (
                        <Link
                            key={item.to}
                            to={item.to}
                            className={`sidebar-link ${isActive ? 'active' : ''}`}
                            title={collapsed ? item.label : undefined}
                        >
                            <Icon size={20} />
                            {!collapsed && <span>{item.label}</span>}
                        </Link>
                    );
                })}
            </nav>

            {/* Bottom items */}
            <div className="sidebar-bottom">
                {BOTTOM_ITEMS.map((item) => {
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.label}
                            to={item.to}
                            className="sidebar-link"
                            title={collapsed ? item.label : undefined}
                        >
                            <Icon size={20} />
                            {!collapsed && <span>{item.label}</span>}
                        </Link>
                    );
                })}

                {/* Collapse toggle */}
                <button
                    className="sidebar-toggle"
                    onClick={() => setCollapsed(!collapsed)}
                    aria-label="Toggle sidebar"
                >
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                    {!collapsed && <span>Collapse</span>}
                </button>
            </div>
        </aside>
    );
}
