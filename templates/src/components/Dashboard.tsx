import { Suspense, lazy, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  CreditCard, 
  MessageSquare, 
  Settings, 
  Plus,
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  Target,
  ArrowUpRight,
  ArrowDownRight,
  MoreVertical,
  ShieldCheck,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { ThemeToggle } from './ThemeToggle';
import { useAuth } from '../store/auth-context';
import { useTheme } from '../store/theme-context';
import { formatCurrency, getGreeting, cn } from '../utils';
import { AnimatedCounter } from './AnimatedCounter';

const PieChart = lazy(() => import('recharts').then(m => ({ default: m.PieChart })));
const Pie = lazy(() => import('recharts').then(m => ({ default: m.Pie })));
const Cell = lazy(() => import('recharts').then(m => ({ default: m.Cell })));
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })));
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })));
const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })));
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })));
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })));
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })));
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })));
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })));
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })));
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })));

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const pieData = [
  { name: 'Food', value: 2400, color: '#4A90E2' },
  { name: 'Transport', value: 1200, color: '#50E3C2' },
  { name: 'Shopping', value: 1800, color: '#F5A623' },
  { name: 'Bills', value: 2200, color: '#9B59B6' },
  { name: 'Other', value: 800, color: '#E74C3C' },
];

const weeklyBalance = [
  { day: 'Mon', balance: 5200 },
  { day: 'Tue', balance: 4800 },
  { day: 'Wed', balance: 5100 },
  { day: 'Thu', balance: 4600 },
  { day: 'Fri', balance: 5400 },
  { day: 'Sat', balance: 5000 },
  { day: 'Sun', balance: 5800 },
];

const categorySpending = [
  { category: 'Food', amount: 2400 },
  { category: 'Transport', amount: 1200 },
  { category: 'Shopping', amount: 1800 },
  { category: 'Bills', amount: 2200 },
  { category: 'Healthcare', amount: 600 },
];

const recentTransactions = [
  { id: 1, name: 'Grocery Store', category: 'Food', amount: -85.5, date: 'Today, 2:30 PM', icon: '🛒' },
  { id: 2, name: 'Salary Deposit', category: 'Income', amount: 3500, date: 'Today, 9:00 AM', icon: '💰' },
  { id: 3, name: 'Uber Ride', category: 'Transport', amount: -15.2, date: 'Yesterday, 6:45 PM', icon: '🚗' },
  { id: 4, name: 'Netflix Subscription', category: 'Entertainment', amount: -12.99, date: 'Oct 29, 2025', icon: '🎬' },
  { id: 5, name: 'Coffee Shop', category: 'Food', amount: -5.8, date: 'Oct 29, 2025', icon: '☕' },
];

export function Dashboard() {
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const navigate = useNavigate();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await new Promise(r => setTimeout(r, 1000));
    setIsRefreshing(false);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 glass-card border-r border-white/10 p-6 hidden lg:block z-40">
        <motion.div 
          className="flex items-center gap-3 mb-8"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg">
            <Wallet className="w-6 h-6 text-white" />
          </div>
          <h1 className="font-['Poppins'] font-bold text-xl bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            FinTech
          </h1>
        </motion.div>

        <nav className="space-y-2">
          {[{ icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
            { icon: CreditCard, label: 'Transactions', path: '/transactions' },
            { icon: MessageSquare, label: 'Messages', path: '/messages' },
            { icon: Settings, label: 'Settings', path: '/settings' }].map((item) => (
            <Button
              key={item.path}
              variant="ghost"
              className="w-full justify-start gap-3 hover:bg-white/10 transition-all duration-200"
              onClick={() => navigate(item.path)}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </Button>
          ))}
        </nav>

        <div className="absolute bottom-6 left-6 right-6">
          <div className="p-4 glass-card rounded-lg border border-white/10">
            <ShieldCheck className="w-8 h-8 text-primary mb-2" />
            <h4 className="font-['Poppins'] font-semibold mb-1">Pro Features</h4>
            <p className="text-sm text-muted-foreground font-['Inter'] mb-3">
              Unlock advanced analytics
            </p>
            <Button size="sm" className="w-full bg-gradient-to-r from-primary to-secondary">
              Upgrade Now
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="glass-card border-b border-white/10 sticky top-0 z-30 backdrop-blur-xl">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <motion.h2 
                  className="font-['Poppins'] font-bold text-2xl"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  Dashboard
                </motion.h2>
                <motion.p 
                  className="text-muted-foreground font-['Inter']"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  {getGreeting(user?.firstName || 'User')}
                </motion.p>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleRefresh}
                  className={cn("rounded-full", isRefreshing && "animate-spin")}
                >
                  <RefreshCw className="h-5 w-5" />
                </Button>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer shadow-lg">
                  <span className="text-white font-['Inter'] font-semibold">
                    {user?.firstName?.[0]}{user?.lastName?.[0]}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {[
              { title: 'Total Balance', value: 5847.32, change: 12.5, icon: Wallet, positive: true },
              { title: 'Total Income', value: 3500, change: 8.2, icon: ArrowUpRight, positive: true },
              { title: 'Total Expenses', value: 2428.5, change: -5.1, icon: ArrowDownRight, positive: false },
              { title: 'Savings Goal', value: 4500, change: 75, icon: Target, positive: true },
            ].map((stat, i) => (
              <motion.div key={stat.title} variants={itemVariants}>
                <Card className="p-6 glass-card hover:shadow-xl transition-all duration-300 border-white/10">
                  <div className="flex items-center justify-between mb-4">
                    <div className={cn(
                      "w-12 h-12 rounded-lg flex items-center justify-center",
                      stat.positive ? "bg-primary/20" : "bg-secondary/20"
                    )}>
                      <stat.icon className={cn(
                        "w-6 h-6",
                        stat.positive ? "text-primary" : "text-secondary"
                      )} />
                    </div>
                    <Badge className={cn(
                      "backdrop-blur-sm",
                      stat.positive ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                    )}>
                      {stat.change > 0 ? '+' : ''}{stat.change}%
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
                    {stat.title}
                  </p>
                  <h3 className="font-['Poppins'] font-bold text-2xl">
                    <AnimatedCounter from={0} to={stat.value} prefix="$" />
                  </h3>
                </Card>
              </motion.div>
            ))}
          </motion.div>

          <motion.div 
            className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={itemVariants}>
              <Card className="p-6 glass-card border-white/10">
                <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Monthly Expenses</h3>
                <Suspense fallback={<div className="h-[280px] animate-pulse bg-white/5 rounded" />}>
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Suspense>
              </Card>
            </motion.div>

            <motion.div variants={itemVariants}>
              <Card className="p-6 glass-card border-white/10">
                <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Weekly Balance</h3>
                <Suspense fallback={<div className="h-[280px] animate-pulse bg-white/5 rounded" />}>
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={weeklyBalance}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="day" stroke="var(--muted-foreground)" />
                      <YAxis stroke="var(--muted-foreground)" />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="balance"
                        stroke="var(--primary)"
                        strokeWidth={3}
                        dot={{ fill: "var(--primary)", r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Suspense>
              </Card>
            </motion.div>
          </motion.div>

          <motion.div 
            className="grid grid-cols-1 lg:grid-cols-3 gap-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div className="lg:col-span-2" variants={itemVariants}>
              <Card className="p-6 glass-card border-white/10">
                <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <Button className="h-auto py-6 flex-col gap-2 bg-gradient-to-r from-primary to-secondary shadow-lg hover:shadow-xl transition-all">
                    <Plus className="w-6 h-6" />
                    <span>Add Transaction</span>
                  </Button>
                  <Button className="h-auto py-6 flex-col gap-2 glass-card hover:bg-white/10 transition-all">
                    <Sparkles className="w-6 h-6" />
                    <span>AI Insights</span>
                  </Button>
                  <Button className="h-auto py-6 flex-col gap-2 glass-card hover:bg-white/10 transition-all">
                    <MessageSquare className="w-6 h-6" />
                    <span>AI Assistant</span>
                  </Button>
                </div>
              </Card>
            </motion.div>
          </motion.div>
        </main>
      </div>
    </div>
  );
}