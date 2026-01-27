import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { ThemeToggle } from "./ThemeToggle";
import {
  Sparkles,
  TrendingUp,
  MessageSquare,
  Shield,
  BarChart3,
  Zap,
  ArrowRight,
} from "lucide-react";

interface LandingPageProps {
  onNavigate: (page: string) => void;
}

export function LandingPage({ onNavigate }: LandingPageProps) {
  const features = [
    {
      icon: Sparkles,
      title: "AI-Powered Insights",
      description: "Get smart recommendations based on your spending patterns",
    },
    {
      icon: TrendingUp,
      title: "Track Your Growth",
      description: "Visualize your financial progress with beautiful charts",
    },
    {
      icon: MessageSquare,
      title: "AI Assistant",
      description: "Chat with your personal finance assistant anytime",
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Your data is encrypted and protected at all times",
    },
    {
      icon: BarChart3,
      title: "Smart Analytics",
      description: "Understand where your money goes with detailed breakdowns",
    },
    {
      icon: Zap,
      title: "Quick Actions",
      description: "Add transactions and tasks in seconds with AI help",
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border backdrop-blur-sm bg-background/80 sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h1 className="font-['Poppins'] font-bold text-xl">Ohmatt</h1>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Button
                variant="ghost"
                onClick={() => onNavigate("login")}
                className="hidden sm:inline-flex"
              >
                Login
              </Button>
              <Button onClick={() => onNavigate("register")}>Sign Up</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
            <Sparkles className="w-4 h-4" />
            <span className="font-['Inter'] font-medium">AI-Powered Finance Management</span>
          </div>
          <h1 className="font-['Poppins'] font-bold text-4xl sm:text-5xl lg:text-6xl mb-6 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
            Take Control of Your Financial Future
          </h1>
          <p className="font-['Inter'] text-lg sm:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Smart budgeting, expense tracking, and AI-powered insights to help you make better financial decisions every day.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              size="lg"
              onClick={() => onNavigate("register")}
              className="w-full sm:w-auto bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-200 group"
            >
              Get Started Free
              <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => onNavigate("dashboard")}
              className="w-full sm:w-auto"
            >
              View Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-['Poppins'] font-bold text-3xl sm:text-4xl mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="font-['Inter'] text-lg text-muted-foreground">
              Powerful features designed to make finance management effortless
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card
                  key={index}
                  className="p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1 border-border bg-card"
                >
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-['Poppins'] font-semibold text-lg mb-2">
                    {feature.title}
                  </h3>
                  <p className="font-['Inter'] text-muted-foreground">
                    {feature.description}
                  </p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 mb-16">
        <Card className="max-w-4xl mx-auto p-8 sm:p-12 bg-gradient-to-br from-primary/5 to-secondary/5 border-primary/20">
          <div className="text-center">
            <h2 className="font-['Poppins'] font-bold text-3xl sm:text-4xl mb-4">
              Ready to Transform Your Finances?
            </h2>
            <p className="font-['Inter'] text-lg text-muted-foreground mb-8">
              Join thousands of users who are already managing their money smarter with AI
            </p>
            <Button
              size="lg"
              onClick={() => onNavigate("register")}
              className="bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-200"
            >
              Start Your Free Trial
            </Button>
          </div>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-muted-foreground font-['Inter']">
            <p>© 2025 Ohmatt. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
