import { ReactNode } from 'react';
import Navigation from './Navigation';
import StatusBar from './StatusBar';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-background">
      <Navigation />
      <div className="flex-1 overflow-auto">
        {children}
      </div>
      <StatusBar />
    </div>
  );
}