import { useMemo, useEffect, useState } from 'react';
import { Link, useRouterState } from '@tanstack/react-router';
import { Bell, BellDot, LayoutDashboard, LogOut, Settings, User, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MessagesDock } from '@/components/messages-dock';
import { EscrowTermsDialog } from '@/components/escrow-terms-dialog';
import { readTermsAgreement } from '@/lib/terms-agreement';
import { signOut, type DemoSession } from '@/lib/demo-session';

const sampleNotifications = [
  { id: 'n1', title: 'Welcome to AiGrid', text: 'Your account is ready. Explore creators and reels.', time: 'Just now' },
  { id: 'n2', title: 'Riddhi Shah liked your reel', text: 'Your work is getting noticed.', time: '12 min ago' },
  { id: 'n3', title: 'New brief matches your skills', text: 'A brand is looking for AI motion work.', time: '1 hr ago' },
  { id: 'n4', title: 'Profile viewed 12 times', text: 'Creators and brands checked your profile this week.', time: 'Yesterday' },
];

export function AccountMenu({ session }: { session: DemoSession }) {
  const isHome = useRouterState({ select: s => s.location.pathname === '/' });
  const [read, setRead] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);

  useEffect(() => {
    const handler = () => setTermsOpen(true);
    window.addEventListener('open-escrow-terms', handler);
    return () => window.removeEventListener('open-escrow-terms', handler);
  }, []);
  const initials = useMemo(() => session.name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase(), [session.name]);
  return <>
    <Popover onOpenChange={open => { if (open) setRead(true); }}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="account-bell" aria-label="Open notifications">
          {read ? <Bell aria-hidden="true" /> : <BellDot aria-hidden="true" />}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="notifications-panel">
        <h2 className="notifications-title">Notifications</h2>
        <ul className="notifications-list">
          {sampleNotifications.map(item => <li key={item.id}>
            <strong>{item.title}</strong>
            <p>{item.text}</p>
            <span>{item.time}</span>
          </li>)}
        </ul>
        <div className="notifications-footer">
          <Button variant="link">View all</Button>
          <Button variant="link">Settings</Button>
        </div>
      </PopoverContent>
    </Popover>
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="account-avatar" aria-label={`Open account menu for ${session.name}`}>
          <i className="account-initials" aria-hidden="true">{initials}</i>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="account-menu">
        <DropdownMenuLabel className="account-menu-head">
          <i className="account-initials" aria-hidden="true">{initials}</i>
          <span><strong>{session.name}</strong><small>{session.email}</small></span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild><Link to="/login"><Settings aria-hidden="true" /> Manage account</Link></DropdownMenuItem>
        <DropdownMenuItem asChild><Link to="/discover"><LayoutDashboard aria-hidden="true" /> Dashboard</Link></DropdownMenuItem>
        <DropdownMenuItem asChild><Link to="/dashboard"><FolderOpen aria-hidden="true" /> Projects &amp; Escrow</Link></DropdownMenuItem>
        <DropdownMenuItem asChild><Link to="/discover"><FolderOpen aria-hidden="true" /> My Work</Link></DropdownMenuItem>
        <DropdownMenuItem asChild><Link to="/creators"><User aria-hidden="true" /> Profile</Link></DropdownMenuItem>
        <DropdownMenuItem asChild><Link to="/discover"><Bell aria-hidden="true" /> Notifications</Link></DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => signOut()}><LogOut aria-hidden="true" /> Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
    <EscrowTermsDialog
      open={termsOpen}
      onOpenChange={setTermsOpen}
      userEmail={session.email}
    />
    {!isHome && <MessagesDock />}
  </>;
}
