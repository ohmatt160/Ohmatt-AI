import { useState, useEffect } from "react";
import { LandingPage } from "./components/LandingPage";
import { LoginPage } from "./components/LoginPage";
import { RegisterPage } from "./components/RegisterPage";
import { Dashboard } from "./components/Dashboard";
import { TransactionView } from "./components/TransactionView";
import { MessagingCenter } from "./components/MessagingCenter";
import { ProfileSettings } from "./components/ProfileSettings";
import { AdminPanel } from "./components/AdminPanel";
import { Toaster } from "./components/ui/sonner";
import {BankConnection} from "./components/BankConnection"
// import jwtDecode from "jwt-decode";
type Page =
  | "landing"
  | "login"
  | "register"
  | "dashboard"
  | "transactions"
  | "messages"
  | "settings"
    
  | "admin";

// interface TokenPayload {
//   exp: number; // expiration time (in seconds)
// }

export default function App() {
 const [currentPage, setCurrentPage] = useState<Page>("landing");

  // Check token on startup
  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setCurrentPage("landing");
      return;
    }

    try {
      const decoded = jwtDecode<TokenPayload>(token);
      const isExpired = decoded.exp * 1000 < Date.now();

      if (isExpired) {
        localStorage.removeItem("token");
        setCurrentPage("login");
      } else {
        // If token valid, restore previous page or go to dashboard
        const savedPage = localStorage.getItem("currentPage") as Page;
        setCurrentPage(savedPage || "dashboard");
      }
    } catch {
      // Invalid token format
      localStorage.removeItem("token");
      setCurrentPage("login");
    }
  }, []);

  // Save current page to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("currentPage", currentPage);
  }, [currentPage]);

  const handleNavigate = (page: string) => {
    setCurrentPage(page as Page);
  };

  const renderPage = () => {
    switch (currentPage) {
      case "landing":
        return <LandingPage onNavigate={handleNavigate} />;
      case "login":
        return <LoginPage onNavigate={handleNavigate} />;
      case 'bank-connection':
        return <BankConnection onNavigate={setCurrentPage} />;
      case "register":
        return <RegisterPage onNavigate={handleNavigate} />;
      case "dashboard":
        return <Dashboard onNavigate={handleNavigate} />;
      case "transactions":
        return <TransactionView onNavigate={handleNavigate} />;
      case "messages":
        return <MessagingCenter onNavigate={handleNavigate} />;
      case "settings":
        return <ProfileSettings onNavigate={handleNavigate} />;
      case "admin":
        return <AdminPanel onNavigate={handleNavigate} />;
      default:
        return <LandingPage onNavigate={handleNavigate} />;
    }
  };

  return (
    <>
      {renderPage()}
      <Toaster />
    </>
  );
}

