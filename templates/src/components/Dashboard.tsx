// // import {  useEffect, useState } from "react";
// // import { Button } from "./ui/button";
// // import { Card } from "./ui/card";
// // import { ThemeToggle } from "./ThemeToggle";
// // import {
// //   LayoutDashboard,
// //   CreditCard,
// //   MessageSquare,
// //   Settings,
// //   Plus,
// //   TrendingUp,
// //   TrendingDown,
// //   Wallet,
// //   Target,
// //   ArrowUpRight,
// //   ArrowDownRight,
// //   MoreVertical,
// //   ShieldCheck,
// // } from "lucide-react";
// // import { Badge } from "./ui/badge";
// // import { Progress } from "./ui/progress";
// // import {
// //   PieChart,
// //   Pie,
// //   Cell,
// //   LineChart,
// //   Line,
// //   BarChart,
// //   Bar,
// //   XAxis,
// //   YAxis,
// //   CartesianGrid,
// //   Tooltip,
// //   ResponsiveContainer,
// //   Legend,
// // } from "recharts";
// // import {
// //   parseISO,
// //   format,
// //   subDays,
// //   eachDayOfInterval,
// //   startOfDay,
// //   endOfDay,
// //   isWithinInterval,
// // } from "date-fns";

// // interface DashboardProps {
// //   onNavigate: (page: string) => void;
// // }

// // interface Task {
// //   id: number;
// //   task: string;
// //   date: string;
// //   time: string;
// // }

// // interface BackendTransaction {
// //   id: number;
// //   description: string; // backend field
// //   amount: number;
// //   date: string; // ISO string expected
// //   category?: string;
// //   ml_confidence?: number;
// // }

// // interface Transaction {
// //   id: number;
// //   name: string;
// //   category?: string;
// //   amount: number;
// //   date: string;
// //   rawDate: string;
// //   icon?: string;
// // }

// // interface TransactionFormData {
// //   description: string;
// //   amount: string;
// //   date: string;
// //   time: string;
// // }

// // export function Dashboard({ onNavigate }: DashboardProps) {
// //   const [activeModal, setActiveModal] = useState<string | null>(null);
// //   const [tasks, setTasks] = useState<Task[]>([]);
// //   const [transactions, setTransactions] = useState<Transaction[]>([]);
// //   const [loading, setLoading] = useState(true);
// //   const [error, setError] = useState<string | null>(null);

// // // Derived / computed UI state
// //   const [totalBalance, setTotalBalance] = useState<number>(0);
// //   const [totalIncome, setTotalIncome] = useState<number>(0);
// //   const [totalExpenses, setTotalExpenses] = useState<number>(0);
// //   const [savingsProgress, setSavingsProgress] = useState<number>(0); // 0 - 100
// //   const [weeklyBalance, setWeeklyBalance] = useState<Array<{ day: string; balance: number }>>([]);
// //   const [categorySpending, setCategorySpending] = useState<Array<{ category: string; amount: number }>>(
// //     []
// //   );
// //   const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
// //   const [pieData, setPieData] = useState<Array<{ name: string; value: number; color?: string }>>([]);

// //   // small palette fallback for pie chart
// //   const COLORS = ["#4A90E2", "#50E3C2", "#F5A623", "#9B59B6", "#E74C3C", "#7F8C8D"];


// //   // 👇 fetch tasks & transactions on load
// //   useEffect(() => {
// //     const fetchData = async () => {
// //       setLoading(true);
// //       setError(null);
// //       try {
// //         const token = localStorage.getItem("token");
// //         if (!token) {
// //           throw new Error("No token found in localStorage");
// //         }

// //         const [taskRes, transactionRes] = await Promise.all([
// //           fetch("http://127.0.0.1:5000/tasks", {
// //             headers: { Authorization: `Bearer ${token}` },
// //           }),
// //           fetch("http://127.0.0.1:5000/transactions", {
// //             headers: { Authorization: `Bearer ${token}` },
// //           }),
// //         ]);

// //         if (!taskRes.ok) {
// //           const txt = await taskRes.text();
// //           throw new Error(`Tasks fetch failed: ${taskRes.status} ${txt}`);
// //         }
// //         if (!transactionRes.ok) {
// //           const txt = await transactionRes.text();
// //           throw new Error(`Transactions fetch failed: ${transactionRes.status} ${txt}`);
// //         }

// //         const taskData = await taskRes.json();
// //         const transactionData = await transactionRes.json();

// //         setTasks(taskData.tasks || []);
// //         // setTransactions(transactionData.transactions || []);

// //         // Transactions: backend might return array or { transactions: [...] }
// //         const backendTransactions: BackendTransaction[] =
// //           Array.isArray(transactionData) ? transactionData : transactionData.transactions || [];

// //         // Map backend shape to UI Transaction shape
// //         const mapped: Transaction[] = backendTransactions.map((t) => {
// //           // ensure date parsing is robust; if no date provided use now
// //           const rawDate = t.date ?? new Date().toISOString();
// //           const friendly = format(parseISO(rawDate), "PPP, p"); // e.g. Oct 29, 2025, 9:00 AM
// //           return {
// //             id: t.id,
// //             name: t.description || t.category || "Transaction",
// //             category: t.category || "Other",
// //             amount: t.amount || 0,
// //             date: friendly,
// //             rawDate,
// //           };
// //         });

// //         // Sort transactions descending by date
// //         mapped.sort((a, b) => (parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime()));

// //         setTransactions(mapped);

// //         // Compute everything derived from transactions
// //         computeDerivedStats(mapped);
// //       } catch (err: any) {
// //         console.error("Error fetching data:", err);
// //         setError(err.message || "Failed to fetch data");
// //       } finally {
// //         setLoading(false);
// //       }
// //     };

// //     fetchData();
// //   }, []);

// //   // // Mock data
// //   // const expenseData = [
// //   //   { name: "Food", value: 2400, color: "#4A90E2" },
// //   //   { name: "Transport", value: 1200, color: "#50E3C2" },
// //   //   { name: "Shopping", value: 1800, color: "#F5A623" },
// //   //   { name: "Bills", value: 2200, color: "#9B59B6" },
// //   //   { name: "Other", value: 800, color: "#E74C3C" },
// //   // ];

// //   // const weeklyBalance = [
// //   //   { day: "Mon", balance: 5200 },
// //   //   { day: "Tue", balance: 4800 },
// //   //   { day: "Wed", balance: 5100 },
// //   //   { day: "Thu", balance: 4600 },
// //   //   { day: "Fri", balance: 5400 },
// //   //   { day: "Sat", balance: 5000 },
// //   //   { day: "Sun", balance: 5800 },
// //   // ];

// //   // const categorySpending = [
// //   //   { category: "Food", amount: 2400 },
// //   //   { category: "Transport", amount: 1200 },
// //   //   { category: "Shopping", amount: 1800 },
// //   //   { category: "Bills", amount: 2200 },
// //   // ];

// //   // const recentTransactions = [
// //   //   {
// //   //     id: 1,
// //   //     name: "Grocery Store",
// //   //     category: "Food",
// //   //     amount: -85.5,
// //   //     date: "Today, 2:30 PM",
// //   //     icon: "🛒",
// //   //   },
// //   //   {
// //   //     id: 2,
// //   //     name: "Salary Deposit",
// //   //     category: "Income",
// //   //     amount: 3500,
// //   //     date: "Today, 9:00 AM",
// //   //     icon: "💰",
// //   //   },
// //   //   {
// //   //     id: 3,
// //   //     name: "Uber Ride",
// //   //     category: "Transport",
// //   //     amount: -15.2,
// //   //     date: "Yesterday, 6:45 PM",
// //   //     icon: "🚗",
// //   //   },
// //   //   {
// //   //     id: 4,
// //   //     name: "Netflix Subscription",
// //   //     category: "Entertainment",
// //   //     amount: -12.99,
// //   //     date: "Oct 29, 2025",
// //   //     icon: "🎬",
// //   //   },
// //   //   {
// //   //     id: 5,
// //   //     name: "Coffee Shop",
// //   //     category: "Food",
// //   //     amount: -5.8,
// //   //     date: "Oct 29, 2025",
// //   //     icon: "☕",
// //   //   },
// //   // ];

// //   // const upcomingTasks = [
// //   //   { id: 1, title: "Pay electricity bill", due: "Tomorrow", priority: "high" },
// //   //   { id: 2, title: "Review monthly budget", due: "Nov 3", priority: "medium" },
// //   //   { id: 3, title: "Set savings goal", due: "Nov 5", priority: "low" },
// //   // ];
// //   //  if (loading) {
// //   //   return (
// //   //     <div className="min-h-screen flex items-center justify-center">
// //   //       <p>Loading dashboard...</p>
// //   //     </div>
// //   //   );
// //   // }


// //   function computeDerivedStats(txns: Transaction[]) {
// //     // Totals
// //     const total = txns.reduce((acc, t) => acc + (t.amount ?? 0), 0);
// //     const income = txns.reduce((acc, t) => acc + (t.amount > 0 ? t.amount : 0), 0);
// //     const expenses = txns.reduce((acc, t) => acc + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);

// //     setTotalBalance(total);
// //     setTotalIncome(income);
// //     setTotalExpenses(expenses);

// //     // Savings progress: simple heuristic: savings = income - expenses; target use e.g. 6000 or computed
// //     const targetSavings = Math.max(4500, income * 0.5); // fallback target
// //     const currentSavings = Math.max(0, income - expenses);
// //     const progress = targetSavings > 0 ? Math.min(100, Math.round((currentSavings / targetSavings) * 100)) : 0;
// //     setSavingsProgress(progress);

// //     // Recent transactions: already sorted desc; take first 5
// //     setRecentTransactions(txns.slice(0, 5));

// //     // Category spending (only negative amounts as spending)
// //     const catMap = new Map<string, number>();
// //     for (const t of txns) {
// //       const cat = t.category || "Other";
// //       const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
// //       catMap.set(cat, (catMap.get(cat) || 0) + amt);
// //     }
// //     const categoryArr = Array.from(catMap.entries()).map(([category, amount]) => ({ category, amount }));
// //     // Sort descending by spend
// //     categoryArr.sort((a, b) => b.amount - a.amount);
// //     setCategorySpending(categoryArr);

// //     // Pie data using categoryArr (top 6)
// //     const pie = categoryArr.slice(0, 6).map((c, i) => ({
// //       name: c.category,
// //       value: c.amount,
// //       color: COLORS[i % COLORS.length],
// //     }));
// //     // If no negative spends exist, show small "Other" slice to avoid empty charts
// //     if (pie.length === 0) {
// //       setPieData([{ name: "Other", value: 1, color: COLORS[0] }]);
// //     } else {
// //       setPieData(pie);
// //     }

// //     // Weekly Balance: compute balance per day over last 7 days (including today)
// //     const today = new Date();
// //     const days = eachDayOfInterval({ start: subDays(startOfDay(today), 6), end: startOfDay(today) });

// //     // create running balance: start from 0 and add day's net (or compute cumulative from transactions)
// //     // Here we'll compute cumulative balance for each day based on transactions up to that day.
// //     // First, create a sorted ascending txns array to compute running balances
// //     const ascTxns = [...txns].sort((a, b) => parseISO(a.rawDate).getTime() - parseISO(b.rawDate).getTime());
// //     const balances: { day: string; balance: number }[] = [];

// //     // compute cumulative balances up to each day
// //     for (const day of days) {
// //       const dayStart = startOfDay(day);
// //       const dayEnd = endOfDay(day);
// //       const dayNet = ascTxns
// //         .filter((t) => isWithinInterval(parseISO(t.rawDate), { start: dayStart, end: dayEnd }))
// //         .reduce((acc, t) => acc + (t.amount ?? 0), 0);

// //       // cumulative balance up to this day is sum of all txns <= dayEnd
// //       const cumulative = ascTxns
// //         .filter((t) => parseISO(t.rawDate) <= dayEnd)
// //         .reduce((acc, t) => acc + (t.amount ?? 0), 0);

// //       balances.push({
// //         day: format(day, "EEE"), // Mon, Tue...
// //         balance: Math.round(cumulative * 100) / 100,
// //       });
// //     }

// //     setWeeklyBalance(balances);
// //   }

// //   if (loading) {
// //     return (
// //       <div className="min-h-screen flex items-center justify-center">
// //         <p>Loading dashboard...</p>
// //       </div>
// //     );
// //   }

// //   if (error) {
// //     return (
// //       <div className="min-h-screen flex items-center justify-center">
// //         <p>Error loading dashboard: {error}</p>
// //       </div>
// //     );
// //   }
// //   const TransactionModal = () => {
// //   const [formData, setFormData] = useState<TransactionFormData>({
// //     description: '',
// //     amount: '',
// //     date: new Date().toISOString().split('T')[0], // Today's date
// //     time: new Date().toTimeString().slice(0, 5), // Current time
// //   });
// //   const [submitting, setSubmitting] = useState(false);
// //   const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

// //   const handleSubmit = async (e: React.FormEvent) => {
// //     e.preventDefault();
// //     setSubmitting(true);
// //     setMessage(null);

// //     try {
// //       const token = localStorage.getItem("token");
// //       if (!token) {
// //         throw new Error("No authentication token found");
// //       }

// //        // Combine date and time into ISO format
// //       const dateTime = `${formData.date}T${formData.time}:00.000Z`;

// //       const transactionData = {
// //         description: formData.description,
// //         amount: parseFloat(formData.amount),
// //         date: dateTime,
// //       };

// //       const response = await fetch("http://127.0.0.1:5000/transactions/add", {
// //         method: "POST",
// //         headers: {
// //           "Content-Type": "application/json",
// //           "Authorization": `Bearer ${token}`,
// //         },
// //         body: JSON.stringify(transactionData),
// //       });

// //       if (!response.ok) {
// //         const errorText = await response.text();
// //         throw new Error(`Failed to add transaction: ${response.status} ${errorText}`);
// //       }

// //       const result = await response.json();

// //       setMessage({
// //         type: 'success',
// //         text: `Transaction added successfully! Category: ${result.transaction_category} (${(result.transaction_confidence * 100).toFixed(1)}% confidence)`
// //       });

// //       // Reset form
// //       setFormData({
// //         description: '',
// //         amount: '',
// //         date: new Date().toISOString().split('T')[0],
// //         time: new Date().toTimeString().slice(0, 5),
// //       });

// //       // Refresh transactions data
// //       setTimeout(() => {
// //         window.location.reload(); // Simple refresh, or you can refetch data
// //       }, 2000);

// //     } catch (err: any) {
// //       console.error("Error adding transaction:", err);
// //       setMessage({
// //         type: 'error',
// //         text: err.message || "Failed to add transaction"
// //       });
// //     } finally {
// //       setSubmitting(false);
// //     }
// //   };

// //   const handleChange = (field: keyof TransactionFormData, value: string) => {
// //     setFormData(prev => ({
// //       ...prev,
// //       [field]: value
// //     }));
// //   };

// //   return (
// //     <div className="min-h-screen bg-background">
// //       {/* Sidebar */}
// //       <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border p-6 hidden lg:block">
// //         <div className="flex items-center gap-2 mb-8">
// //           <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
// //             <Wallet className="w-6 h-6 text-white" />
// //           </div>
// //           <h1 className="font-['Poppins'] font-bold text-xl">Ohmatt</h1>
// //         </div>

// //         <nav className="space-y-2">
// //           <Button
// //             variant="default"
// //             className="w-full justify-start gap-3 bg-primary text-primary-foreground"
// //           >
// //             <LayoutDashboard className="w-5 h-5" />
// //             Dashboard
// //           </Button>
// //           <Button
// //             variant="ghost"
// //             className="w-full justify-start gap-3"
// //             onClick={() => onNavigate("transactions")}
// //           >
// //             <CreditCard className="w-5 h-5" />
// //             Transactions
// //           </Button>
// //           <Button
// //             variant="ghost"
// //             className="w-full justify-start gap-3"
// //             onClick={() => onNavigate("messages")}
// //           >
// //             <MessageSquare className="w-5 h-5" />
// //             Messages
// //             <Badge className="ml-auto bg-accent">3</Badge>
// //           </Button>
// //           <Button
// //             variant="ghost"
// //             className="w-full justify-start gap-3"
// //             onClick={() => onNavigate("settings")}
// //           >
// //             <Settings className="w-5 h-5" />
// //             Settings
// //           </Button>
// //         </nav>

// //         <div className="mt-8 p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg border border-primary/20">
// //           <ShieldCheck className="w-8 h-8 text-primary mb-2" />
// //           <h4 className="font-['Poppins'] font-semibold mb-1">Pro Features</h4>
// //           <p className="text-sm text-muted-foreground mb-3 font-['Inter']">
// //             Unlock advanced analytics and insights
// //           </p>
// //           <Button size="sm" className="w-full bg-primary">
// //             Upgrade Now
// //           </Button>
// //         </div>
// //       </aside>

// //       {/* Main Content */}
// //       <div className="lg:ml-64">
// //         {/* Header */}
// //         <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
// //           <div className="px-4 sm:px-6 lg:px-8 py-4">
// //             <div className="flex items-center justify-between">
// //               <div>
// //                 <h2 className="font-['Poppins'] font-bold text-2xl">Dashboard</h2>
// //                 <p className="text-muted-foreground font-['Inter']">
// //                   Welcome back, John! Here's your financial overview.
// //                 </p>
// //               </div>
// //               <div className="flex items-center gap-3">
// //                 <ThemeToggle />
// //                 <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
// //                   <span className="text-white font-['Inter'] font-semibold">JD</span>
// //                 </div>
// //               </div>
// //             </div>
// //           </div>
// //         </header>

// //         {/* Content */}
// //         <main className="p-4 sm:p-6 lg:p-8">
// //           {/* Stats Cards */}
// //           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
// //                   <Wallet className="w-6 h-6 text-primary" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
// //                   <TrendingUp className="w-3 h-3 mr-1" />
// //                   +12.5%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Total Balance
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">$5,847.32</h3>
// //             </Card>

// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
// //                   <ArrowUpRight className="w-6 h-6 text-secondary" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
// //                   <TrendingUp className="w-3 h-3 mr-1" />
// //                   +8.2%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Total Income
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">$3,500.00</h3>
// //             </Card>

// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
// //                   <ArrowDownRight className="w-6 h-6 text-accent" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
// //                   <TrendingDown className="w-3 h-3 mr-1" />
// //                   -5.1%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Total Expenses
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">$2,428.50</h3>
// //             </Card>

// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
// //                   <Target className="w-6 h-6 text-primary" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
// //                   75%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Savings Goal
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">$4,500</h3>
// //             </Card>
// //           </div>

// //           {/* Charts Section */}
// //           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
// //             {/* Monthly Expenses Chart */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Monthly Expenses
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Breakdown by category
// //                   </p>
// //                 </div>
// //                 <Button variant="ghost" size="icon">
// //                   <MoreVertical className="w-4 h-4" />
// //                 </Button>
// //               </div>
// //               <ResponsiveContainer width="100%" height={280}>
// //                 <PieChart>
// //                   <Pie
// //                     data={pieData}
// //                     cx="50%"
// //                     cy="50%"
// //                     innerRadius={60}
// //                     outerRadius={100}
// //                     paddingAngle={5}
// //                     dataKey="value"
// //                   >
// //                     {pieData.map((entry, index) => (
// //                       <Cell key={`cell-${index}`} fill={entry.color} />
// //                     ))}
// //                   </Pie>
// //                   <Tooltip />
// //                   <Legend />
// //                 </PieChart>
// //               </ResponsiveContainer>
// //             </Card>

// //             {/* Weekly Balance Chart */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Weekly Balance
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Balance trend over the week
// //                   </p>
// //                 </div>
// //                 <Button variant="ghost" size="icon">
// //                   <MoreVertical className="w-4 h-4" />
// //                 </Button>
// //               </div>
// //               <ResponsiveContainer width="100%" height={280}>
// //                 <LineChart data={weeklyBalance}>
// //                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
// //                   <XAxis dataKey="day" stroke="var(--color-muted-foreground)" />
// //                   <YAxis stroke="var(--color-muted-foreground)" />
// //                   <Tooltip
// //                     contentStyle={{
// //                       backgroundColor: "var(--color-card)",
// //                       border: "1px solid var(--color-border)",
// //                       borderRadius: "8px",
// //                     }}
// //                   />
// //                   <Line
// //                     type="monotone"
// //                     dataKey="balance"
// //                     stroke="#4A90E2"
// //                     strokeWidth={3}
// //                     dot={{ fill: "#4A90E2", r: 5 }}
// //                   />
// //                 </LineChart>
// //               </ResponsiveContainer>
// //             </Card>

// //             {/* Category Spending Chart */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Category Spending
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Top spending categories
// //                   </p>
// //                 </div>
// //                 <Button variant="ghost" size="icon">
// //                   <MoreVertical className="w-4 h-4" />
// //                 </Button>
// //               </div>
// //               <ResponsiveContainer width="100%" height={280}>
// //                 <BarChart data={categorySpending}>
// //                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
// //                   <XAxis dataKey="category" stroke="var(--color-muted-foreground)" />
// //                   <YAxis stroke="var(--color-muted-foreground)" />
// //                   <Tooltip
// //                     contentStyle={{
// //                       backgroundColor: "var(--color-card)",
// //                       border: "1px solid var(--color-border)",
// //                       borderRadius: "8px",
// //                     }}
// //                   />
// //                   <Bar dataKey="amount" fill="#4A90E2" radius={[8, 8, 0, 0]} />
// //                 </BarChart>
// //               </ResponsiveContainer>
// //             </Card>

// //             {/* Recent Transactions */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Recent Transactions
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Latest activity
// //                   </p>
// //                 </div>
// //                 <Button
// //                   variant="ghost"
// //                   size="sm"
// //                   onClick={() => onNavigate("transactions")}
// //                 >
// //                   View All
// //                 </Button>
// //               </div>
// //               <div className="space-y-4">
// //                 {recentTransactions.map((transaction) => (
// //                   <div
// //                     key={transaction.id}
// //                     className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
// //                   >
// //                     <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-xl">
// //                       {transaction.icon}
// //                     </div>
// //                     <div className="flex-1 min-w-0">
// //                       <p className="font-['Inter'] font-medium truncate">
// //                         {transaction.name}
// //                       </p>
// //                       <p className="text-sm text-muted-foreground font-['Inter']">
// //                         {transaction.date}
// //                       </p>
// //                     </div>
// //                     <div
// //                       className={`font-['Inter'] font-semibold ${
// //                         transaction.amount > 0 ? "text-secondary" : "text-foreground"
// //                       }`}
// //                     >
// //                       {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
// //                     </div>
// //                   </div>
// //                 ))}
// //               </div>
// //             </Card>
// //           </div>

// //           {/* Quick Actions & Tasks */}
// //           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
// //             {/* Quick Actions */}
// //             <Card className="p-6 border-border bg-card lg:col-span-2">
// //               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Quick Actions</h3>
// //               <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
// //                 <Button
// //                   className="h-auto py-6 flex-col gap-2 bg-primary hover:bg-primary/90 shadow-md hover:shadow-lg transition-all"
// //                   onClick={() => setActiveModal("transaction")}

// //                 >
// //                   <Plus className="w-6 h-6" />
// //                   <span>Add Transaction</span>
// //                 </Button>
// //                 <Button
// //                   className="h-auto py-6 flex-col gap-2 bg-secondary hover:bg-secondary/90 text-secondary-foreground shadow-md hover:shadow-lg transition-all"
// //                   onClick={() => setActiveModal("task")}
// //                 >
// //                   <Plus className="w-6 h-6" />
// //                   <span>Add Task</span>
// //                 </Button>
// //                 <Button
// //                   className="h-auto py-6 flex-col gap-2 bg-accent hover:bg-accent/90 shadow-md hover:shadow-lg transition-all"
// //                   onClick={() => onNavigate("messages")}
// //                 >
// //                   <MessageSquare className="w-6 h-6" />
// //                   <span>AI Assistant</span>
// //                 </Button>

// //               </div>
// //             </Card>

// //             {/* Upcoming Tasks */}
// //             <Card className="p-6 border-border bg-card">
// //               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Upcoming Tasks</h3>
// //               <div className="space-y-3">
// //                 {tasks.map((task) => (
// //                   <div
// //                     key={task.id}
// //                     className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
// //                   >
// //                     <div className="flex items-start gap-3">
// //                       <input
// //                         type="checkbox"
// //                         className="mt-1 w-4 h-4 rounded border-border"
// //                       />
// //                       <div className="flex-1">
// //                         <p className="font-['Inter'] font-medium">{task.title}</p>
// //                         <div className="flex items-center gap-2 mt-1">
// //                           <p className="text-xs text-muted-foreground">{task.due}</p>
// //                           <Badge
// //                             variant="outline"
// //                             className={
// //                               task.priority === "high"
// //                                 ? "bg-red-500/10 text-red-600 border-red-500/20"
// //                                 : task.priority === "medium"
// //                                 ? "bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
// //                                 : "bg-green-500/10 text-green-600 border-green-500/20"
// //                             }
// //                           >
// //                             {task.priority}
// //                           </Badge>
// //                         </div>
// //                       </div>
// //                     </div>
// //                   </div>
// //                 ))}
// //               </div>
// //             </Card>
// //           </div>
// //         </main>
// //       </div>

// //       {/* Modals would be rendered here */}
// //       {activeModal && (
// //         <div
// //           className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
// //           onClick={() => setActiveModal(null)}
// //         >
// //           <div
// //             className="bg-card rounded-xl p-6 max-w-md w-full"
// //             onClick={(e) => e.stopPropagation()}
// //           >
// //             <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
// //               {activeModal === "transaction" ? "Add Transaction" : "Add Task"}
// //             </h3>
// //             <p className="text-muted-foreground">
// //               Modal content would go here. Click outside to close.
// //             </p>
// //           </div>
// //         </div>
// //       )}
// //     </div>
// //   );
// // }



// // import { useEffect, useState } from "react";
// // import { Button } from "./ui/button";
// // import { Card } from "./ui/card";
// // import { ThemeToggle } from "./ThemeToggle";
// // import {
// //   LayoutDashboard,
// //   CreditCard,
// //   MessageSquare,
// //   Settings,
// //   Plus,
// //   TrendingUp,
// //   TrendingDown,
// //   Wallet,
// //   Target,
// //   ArrowUpRight,
// //   ArrowDownRight,
// //   MoreVertical,
// //   ShieldCheck,
// // } from "lucide-react";
// // import { Badge } from "./ui/badge";
// // import { Progress } from "./ui/progress";
// // import {
// //   PieChart,
// //   Pie,
// //   Cell,
// //   LineChart,
// //   Line,
// //   BarChart,
// //   Bar,
// //   XAxis,
// //   YAxis,
// //   CartesianGrid,
// //   Tooltip,
// //   ResponsiveContainer,
// //   Legend,
// // } from "recharts";
// // import {
// //   parseISO,
// //   format,
// //   subDays,
// //   eachDayOfInterval,
// //   startOfDay,
// //   endOfDay,
// //   isWithinInterval,
// // } from "date-fns";

// // interface DashboardProps {
// //   onNavigate: (page: string) => void;
// // }

// // interface Task {
// //   id: number;
// //   task: string;
// //   date: string;
// //   time: string;
// // }

// // interface BackendTransaction {
// //   id: number;
// //   description: string;
// //   amount: number;
// //   date: string;
// //   category?: string;
// //   ml_confidence?: number;
// // }

// // interface Transaction {
// //   id: number;
// //   name: string;
// //   category?: string;
// //   amount: number;
// //   date: string;
// //   rawDate: string;
// //   icon?: string;
// // }

// // interface TransactionFormData {
// //   description: string;
// //   amount: string;
// //   date: string;
// //   time: string;
// // }

// // export function Dashboard({ onNavigate }: DashboardProps) {
// //   const [activeModal, setActiveModal] = useState<string | null>(null);
// //   const [tasks, setTasks] = useState<Task[]>([]);
// //   const [transactions, setTransactions] = useState<Transaction[]>([]);
// //   const [loading, setLoading] = useState(true);
// //   const [error, setError] = useState<string | null>(null);

// //   // Derived / computed UI state
// //   const [totalBalance, setTotalBalance] = useState<number>(0);
// //   const [totalIncome, setTotalIncome] = useState<number>(0);
// //   const [totalExpenses, setTotalExpenses] = useState<number>(0);
// //   const [savingsProgress, setSavingsProgress] = useState<number>(0);
// //   const [weeklyBalance, setWeeklyBalance] = useState<Array<{ day: string; balance: number }>>([]);
// //   const [categorySpending, setCategorySpending] = useState<Array<{ category: string; amount: number }>>([]);
// //   const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
// //   const [pieData, setPieData] = useState<Array<{ name: string; value: number; color?: string }>>([]);

// //   const COLORS = ["#4A90E2", "#50E3C2", "#F5A623", "#9B59B6", "#E74C3C", "#7F8C8D"];

// //   // Transaction Modal Component
// //   const TransactionModal = () => {
// //     const [formData, setFormData] = useState<TransactionFormData>({
// //       description: '',
// //       amount: '',
// //       date: new Date().toISOString().split('T')[0],
// //       time: new Date().toTimeString().slice(0, 5),
// //     });
// //     const [submitting, setSubmitting] = useState(false);
// //     const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

// //     const handleSubmit = async (e: React.FormEvent) => {
// //       e.preventDefault();
// //       setSubmitting(true);
// //       setMessage(null);

// //       try {
// //         const token = localStorage.getItem("token");
// //         if (!token) {
// //           throw new Error("No authentication token found");
// //         }

// //         // Combine date and time into ISO format
// //         const dateTime = `${formData.date}T${formData.time}:00.000Z`;

// //         const transactionData = {
// //           description: formData.description,
// //           amount: parseFloat(formData.amount),
// //           date: dateTime,
// //         };

// //         const response = await fetch("http://127.0.0.1:5000/transactions/add", {
// //           method: "POST",
// //           headers: {
// //             "Content-Type": "application/json",
// //             "Authorization": `Bearer ${token}`,
// //           },
// //           body: JSON.stringify(transactionData),
// //         });

// //         if (!response.ok) {
// //           const errorText = await response.text();
// //           throw new Error(`Failed to add transaction: ${response.status} ${errorText}`);
// //         }

// //         const result = await response.json();

// //         setMessage({
// //           type: 'success',
// //           text: `Transaction added successfully! Category: ${result.transaction_category} (${(result.transaction_confidence * 100).toFixed(1)}% confidence)`
// //         });

// //         // Reset form
// //         setFormData({
// //           description: '',
// //           amount: '',
// //           date: new Date().toISOString().split('T')[0],
// //           time: new Date().toTimeString().slice(0, 5),
// //         });

// //         // Refresh transactions data
// //         setTimeout(() => {
// //           window.location.reload();
// //         }, 2000);

// //       } catch (err: any) {
// //         console.error("Error adding transaction:", err);
// //         setMessage({
// //           type: 'error',
// //           text: err.message || "Failed to add transaction"
// //         });
// //       } finally {
// //         setSubmitting(false);
// //       }
// //     };

// //     const handleChange = (field: keyof TransactionFormData, value: string) => {
// //       setFormData(prev => ({
// //         ...prev,
// //         [field]: value
// //       }));
// //     };

// //     return (
// //       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
// //         <div
// //           className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
// //           onClick={(e) => e.stopPropagation()}
// //         >
// //           <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
// //             Add New Transaction
// //           </h3>

// //           <form onSubmit={handleSubmit} className="space-y-4">
// //             <div>
// //               <label className="block text-sm font-medium mb-2 font-['Inter']">
// //                 Description *
// //               </label>
// //               <input
// //                 type="text"
// //                 required
// //                 value={formData.description}
// //                 onChange={(e) => handleChange('description', e.target.value)}
// //                 placeholder="e.g., Grocery shopping, Salary, etc."
// //                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
// //               />
// //             </div>

// //             <div>
// //               <label className="block text-sm font-medium mb-2 font-['Inter']">
// //                 Amount *
// //               </label>
// //               <input
// //                 type="number"
// //                 step="0.01"
// //                 required
// //                 value={formData.amount}
// //                 onChange={(e) => handleChange('amount', e.target.value)}
// //                 placeholder="0.00"
// //                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
// //               />
// //               <p className="text-xs text-muted-foreground mt-1">
// //                 Use positive for income, negative for expenses (e.g., -50.00)
// //               </p>
// //             </div>

// //             <div className="grid grid-cols-2 gap-4">
// //               <div>
// //                 <label className="block text-sm font-medium mb-2 font-['Inter']">
// //                   Date
// //                 </label>
// //                 <input
// //                   type="date"
// //                   value={formData.date}
// //                   onChange={(e) => handleChange('date', e.target.value)}
// //                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
// //                 />
// //               </div>

// //               <div>
// //                 <label className="block text-sm font-medium mb-2 font-['Inter']">
// //                   Time
// //                 </label>
// //                 <input
// //                   type="time"
// //                   value={formData.time}
// //                   onChange={(e) => handleChange('time', e.target.value)}
// //                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
// //                 />
// //               </div>
// //             </div>

// //             {message && (
// //               <div className={`p-3 rounded-lg ${
// //                 message.type === 'success' 
// //                   ? 'bg-green-500/10 text-green-600 border border-green-500/20' 
// //                   : 'bg-red-500/10 text-red-600 border border-red-500/20'
// //               }`}>
// //                 <p className="text-sm font-['Inter']">{message.text}</p>
// //               </div>
// //             )}

// //             <div className="flex gap-3 pt-2">
// //               <Button
// //                 type="button"
// //                 variant="outline"
// //                 className="flex-1"
// //                 onClick={() => setActiveModal(null)}
// //                 disabled={submitting}
// //               >
// //                 Cancel
// //               </Button>
// //               <Button
// //                 type="submit"
// //                 className="flex-1 bg-primary hover:bg-primary/90"
// //                 disabled={submitting}
// //               >
// //                 {submitting ? "Adding..." : "Add Transaction"}
// //               </Button>
// //             </div>
// //           </form>
// //         </div>
// //       </div>
// //     );
// //   };

// //   // Task Modal Component
// //   const TaskModal = () => {
// //     return (
// //       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
// //         <div
// //           className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
// //           onClick={(e) => e.stopPropagation()}
// //         >
// //           <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
// //             Add Task
// //           </h3>
// //           <p className="text-muted-foreground">
// //             Task functionality coming soon...
// //           </p>
// //           <div className="flex gap-3 mt-4">
// //             <Button
// //               variant="outline"
// //               className="flex-1"
// //               onClick={() => setActiveModal(null)}
// //             >
// //               Cancel
// //             </Button>
// //             <Button className="flex-1" disabled>
// //               Add Task
// //             </Button>
// //           </div>
// //         </div>
// //       </div>
// //     );
// //   };

// //   // Fetch data on component mount
// //   useEffect(() => {
// //     const fetchData = async () => {
// //       setLoading(true);
// //       setError(null);
// //       try {
// //         const token = localStorage.getItem("token");
// //         if (!token) {
// //           throw new Error("No token found in localStorage");
// //         }

// //         const [taskRes, transactionRes] = await Promise.all([
// //           fetch("http://127.0.0.1:5000/tasks", {
// //             headers: { Authorization: `Bearer ${token}` },
// //           }),
// //           fetch("http://127.0.0.1:5000/transactions", {
// //             headers: { Authorization: `Bearer ${token}` },
// //           }),
// //         ]);

// //         if (!taskRes.ok) {
// //           const txt = await taskRes.text();
// //           throw new Error(`Tasks fetch failed: ${taskRes.status} ${txt}`);
// //         }
// //         if (!transactionRes.ok) {
// //           const txt = await transactionRes.text();
// //           throw new Error(`Transactions fetch failed: ${transactionRes.status} ${txt}`);
// //         }

// //         const taskData = await taskRes.json();
// //         const transactionData = await transactionRes.json();

// //         setTasks(taskData.tasks || []);

// //         const backendTransactions: BackendTransaction[] =
// //           Array.isArray(transactionData) ? transactionData : transactionData.transactions || [];

// //         const mapped: Transaction[] = backendTransactions.map((t) => {
// //           const rawDate = t.date ?? new Date().toISOString();
// //           const friendly = format(parseISO(rawDate), "PPP, p");
// //           return {
// //             id: t.id,
// //             name: t.description || t.category || "Transaction",
// //             category: t.category || "Other",
// //             amount: t.amount || 0,
// //             date: friendly,
// //             rawDate,
// //           };
// //         });

// //         mapped.sort((a, b) => (parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime()));
// //         setTransactions(mapped);
// //         computeDerivedStats(mapped);
// //       } catch (err: any) {
// //         console.error("Error fetching data:", err);
// //         setError(err.message || "Failed to fetch data");
// //       } finally {
// //         setLoading(false);
// //       }
// //     };

// //     fetchData();
// //   }, []);

// //   function computeDerivedStats(txns: Transaction[]) {
// //     const total = txns.reduce((acc, t) => acc + (t.amount ?? 0), 0);
// //     const income = txns.reduce((acc, t) => acc + (t.amount > 0 ? t.amount : 0), 0);
// //     const expenses = txns.reduce((acc, t) => acc + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);

// //     setTotalBalance(total);
// //     setTotalIncome(income);
// //     setTotalExpenses(expenses);

// //     const targetSavings = Math.max(4500, income * 0.5);
// //     const currentSavings = Math.max(0, income - expenses);
// //     const progress = targetSavings > 0 ? Math.min(100, Math.round((currentSavings / targetSavings) * 100)) : 0;
// //     setSavingsProgress(progress);

// //     setRecentTransactions(txns.slice(0, 5));

// //     const catMap = new Map<string, number>();
// //     for (const t of txns) {
// //       const cat = t.category || "Other";
// //       const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
// //       catMap.set(cat, (catMap.get(cat) || 0) + amt);
// //     }
// //     const categoryArr = Array.from(catMap.entries()).map(([category, amount]) => ({ category, amount }));
// //     categoryArr.sort((a, b) => b.amount - a.amount);
// //     setCategorySpending(categoryArr);

// //     const pie = categoryArr.slice(0, 6).map((c, i) => ({
// //       name: c.category,
// //       value: c.amount,
// //       color: COLORS[i % COLORS.length],
// //     }));
// //     if (pie.length === 0) {
// //       setPieData([{ name: "Other", value: 1, color: COLORS[0] }]);
// //     } else {
// //       setPieData(pie);
// //     }

// //     const today = new Date();
// //     const days = eachDayOfInterval({ start: subDays(startOfDay(today), 6), end: startOfDay(today) });
// //     const ascTxns = [...txns].sort((a, b) => parseISO(a.rawDate).getTime() - parseISO(b.rawDate).getTime());
// //     const balances: { day: string; balance: number }[] = [];

// //     for (const day of days) {
// //       const dayStart = startOfDay(day);
// //       const dayEnd = endOfDay(day);
// //       const cumulative = ascTxns
// //         .filter((t) => parseISO(t.rawDate) <= dayEnd)
// //         .reduce((acc, t) => acc + (t.amount ?? 0), 0);

// //       balances.push({
// //         day: format(day, "EEE"),
// //         balance: Math.round(cumulative * 100) / 100,
// //       });
// //     }

// //     setWeeklyBalance(balances);
// //   }

// //   if (loading) {
// //     return (
// //       <div className="min-h-screen flex items-center justify-center">
// //         <p>Loading dashboard...</p>
// //       </div>
// //     );
// //   }

// //   if (error) {
// //     return (
// //       <div className="min-h-screen flex items-center justify-center">
// //         <p>Error loading dashboard: {error}</p>
// //       </div>
// //     );
// //   }

// //   return (
// //     <div className="min-h-screen bg-background">
// //       {/* Sidebar */}
// //       <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border p-6 hidden lg:block">
// //         <div className="flex items-center gap-2 mb-8">
// //           <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
// //             <Wallet className="w-6 h-6 text-white" />
// //           </div>
// //           <h1 className="font-['Poppins'] font-bold text-xl">Ohmatt</h1>
// //         </div>

// //         <nav className="space-y-2">
// //           <Button
// //             variant="default"
// //             className="w-full justify-start gap-3 bg-primary text-primary-foreground"
// //           >
// //             <LayoutDashboard className="w-5 h-5" />
// //             Dashboard
// //           </Button>
// //           <Button
// //             variant="ghost"
// //             className="w-full justify-start gap-3"
// //             onClick={() => onNavigate("transactions")}
// //           >
// //             <CreditCard className="w-5 h-5" />
// //             Transactions
// //           </Button>
// //           <Button
// //             variant="ghost"
// //             className="w-full justify-start gap-3"
// //             onClick={() => onNavigate("messages")}
// //           >
// //             <MessageSquare className="w-5 h-5" />
// //             Messages
// //             <Badge className="ml-auto bg-accent">3</Badge>
// //           </Button>
// //           <Button
// //             variant="ghost"
// //             className="w-full justify-start gap-3"
// //             onClick={() => onNavigate("settings")}
// //           >
// //             <Settings className="w-5 h-5" />
// //             Settings
// //           </Button>
// //         </nav>

// //         <div className="mt-8 p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg border border-primary/20">
// //           <ShieldCheck className="w-8 h-8 text-primary mb-2" />
// //           <h4 className="font-['Poppins'] font-semibold mb-1">Pro Features</h4>
// //           <p className="text-sm text-muted-foreground mb-3 font-['Inter']">
// //             Unlock advanced analytics and insights
// //           </p>
// //           <Button size="sm" className="w-full bg-primary">
// //             Upgrade Now
// //           </Button>
// //         </div>
// //       </aside>

// //       {/* Main Content */}
// //       <div className="lg:ml-64">
// //         {/* Header */}
// //         <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
// //           <div className="px-4 sm:px-6 lg:px-8 py-4">
// //             <div className="flex items-center justify-between">
// //               <div>
// //                 <h2 className="font-['Poppins'] font-bold text-2xl">Dashboard</h2>
// //                 <p className="text-muted-foreground font-['Inter']">
// //                   Welcome back! Here's your financial overview.
// //                 </p>
// //               </div>
// //               <div className="flex items-center gap-3">
// //                 <ThemeToggle />
// //                 <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
// //                   <span className="text-white font-['Inter'] font-semibold">JD</span>
// //                 </div>
// //               </div>
// //             </div>
// //           </div>
// //         </header>

// //         {/* Content */}
// //         <main className="p-4 sm:p-6 lg:p-8">
// //           {/* Stats Cards */}
// //           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
// //                   <Wallet className="w-6 h-6 text-primary" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
// //                   <TrendingUp className="w-3 h-3 mr-1" />
// //                   +12.5%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Total Balance
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">${totalBalance.toFixed(2)}</h3>
// //             </Card>

// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
// //                   <ArrowUpRight className="w-6 h-6 text-secondary" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
// //                   <TrendingUp className="w-3 h-3 mr-1" />
// //                   +8.2%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Total Income
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">${totalIncome.toFixed(2)}</h3>
// //             </Card>

// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
// //                   <ArrowDownRight className="w-6 h-6 text-accent" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
// //                   <TrendingDown className="w-3 h-3 mr-1" />
// //                   -5.1%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Total Expenses
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">${totalExpenses.toFixed(2)}</h3>
// //             </Card>

// //             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
// //               <div className="flex items-center justify-between mb-4">
// //                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
// //                   <Target className="w-6 h-6 text-primary" />
// //                 </div>
// //                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
// //                   {savingsProgress}%
// //                 </Badge>
// //               </div>
// //               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
// //                 Savings Goal
// //               </p>
// //               <h3 className="font-['Poppins'] font-bold text-2xl">${(totalIncome * 0.5).toFixed(0)}</h3>
// //             </Card>
// //           </div>

// //           {/* Charts Section */}
// //           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
// //             {/* Monthly Expenses Chart */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Monthly Expenses
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Breakdown by category
// //                   </p>
// //                 </div>
// //                 <Button variant="ghost" size="icon">
// //                   <MoreVertical className="w-4 h-4" />
// //                 </Button>
// //               </div>
// //               <ResponsiveContainer width="100%" height={280}>
// //                 <PieChart>
// //                   <Pie
// //                     data={pieData}
// //                     cx="50%"
// //                     cy="50%"
// //                     innerRadius={60}
// //                     outerRadius={100}
// //                     paddingAngle={5}
// //                     dataKey="value"
// //                   >
// //                     {pieData.map((entry, index) => (
// //                       <Cell key={`cell-${index}`} fill={entry.color} />
// //                     ))}
// //                   </Pie>
// //                   <Tooltip />
// //                   <Legend />
// //                 </PieChart>
// //               </ResponsiveContainer>
// //             </Card>

// //             {/* Weekly Balance Chart */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Weekly Balance
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Balance trend over the week
// //                   </p>
// //                 </div>
// //                 <Button variant="ghost" size="icon">
// //                   <MoreVertical className="w-4 h-4" />
// //                 </Button>
// //               </div>
// //               <ResponsiveContainer width="100%" height={280}>
// //                 <LineChart data={weeklyBalance}>
// //                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
// //                   <XAxis dataKey="day" stroke="var(--color-muted-foreground)" />
// //                   <YAxis stroke="var(--color-muted-foreground)" />
// //                   <Tooltip
// //                     contentStyle={{
// //                       backgroundColor: "var(--color-card)",
// //                       border: "1px solid var(--color-border)",
// //                       borderRadius: "8px",
// //                     }}
// //                   />
// //                   <Line
// //                     type="monotone"
// //                     dataKey="balance"
// //                     stroke="#4A90E2"
// //                     strokeWidth={3}
// //                     dot={{ fill: "#4A90E2", r: 5 }}
// //                   />
// //                 </LineChart>
// //               </ResponsiveContainer>
// //             </Card>

// //             {/* Category Spending Chart */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Category Spending
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Top spending categories
// //                   </p>
// //                 </div>
// //                 <Button variant="ghost" size="icon">
// //                   <MoreVertical className="w-4 h-4" />
// //                 </Button>
// //               </div>
// //               <ResponsiveContainer width="100%" height={280}>
// //                 <BarChart data={categorySpending}>
// //                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
// //                   <XAxis dataKey="category" stroke="var(--color-muted-foreground)" />
// //                   <YAxis stroke="var(--color-muted-foreground)" />
// //                   <Tooltip
// //                     contentStyle={{
// //                       backgroundColor: "var(--color-card)",
// //                       border: "1px solid var(--color-border)",
// //                       borderRadius: "8px",
// //                     }}
// //                   />
// //                   <Bar dataKey="amount" fill="#4A90E2" radius={[8, 8, 0, 0]} />
// //                 </BarChart>
// //               </ResponsiveContainer>
// //             </Card>

// //             {/* Recent Transactions */}
// //             <Card className="p-6 border-border bg-card">
// //               <div className="flex items-center justify-between mb-6">
// //                 <div>
// //                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
// //                     Recent Transactions
// //                   </h3>
// //                   <p className="text-sm text-muted-foreground font-['Inter']">
// //                     Latest activity
// //                   </p>
// //                 </div>
// //                 <Button
// //                   variant="ghost"
// //                   size="sm"
// //                   onClick={() => onNavigate("transactions")}
// //                 >
// //                   View All
// //                 </Button>
// //               </div>
// //               <div className="space-y-4">
// //                 {recentTransactions.map((transaction) => (
// //                   <div
// //                     key={transaction.id}
// //                     className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
// //                   >
// //                     <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-xl">
// //                       {transaction.icon}
// //                     </div>
// //                     <div className="flex-1 min-w-0">
// //                       <p className="font-['Inter'] font-medium truncate">
// //                         {transaction.name}
// //                       </p>
// //                       <p className="text-sm text-muted-foreground font-['Inter']">
// //                         {transaction.date}
// //                       </p>
// //                     </div>
// //                     <div
// //                       className={`font-['Inter'] font-semibold ${
// //                         transaction.amount > 0 ? "text-secondary" : "text-foreground"
// //                       }`}
// //                     >
// //                       {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
// //                     </div>
// //                   </div>
// //                 ))}
// //               </div>
// //             </Card>
// //           </div>

// //           {/* Quick Actions & Tasks */}
// //           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
// //             {/* Quick Actions */}
// //             <Card className="p-6 border-border bg-card lg:col-span-2">
// //               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Quick Actions</h3>
// //               <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
// //                 <Button
// //                   className="h-auto py-6 flex-col gap-2 bg-primary hover:bg-primary/90 shadow-md hover:shadow-lg transition-all"
// //                   onClick={() => setActiveModal("transaction")}
// //                 >
// //                   <Plus className="w-6 h-6" />
// //                   <span>Add Transaction</span>
// //                 </Button>
// //                 <Button
// //                   className="h-auto py-6 flex-col gap-2 bg-secondary hover:bg-secondary/90 text-secondary-foreground shadow-md hover:shadow-lg transition-all"
// //                   onClick={() => setActiveModal("task")}
// //                 >
// //                   <Plus className="w-6 h-6" />
// //                   <span>Add Task</span>
// //                 </Button>
// //                 <Button
// //                   className="h-auto py-6 flex-col gap-2 bg-accent hover:bg-accent/90 shadow-md hover:shadow-lg transition-all"
// //                   onClick={() => onNavigate("messages")}
// //                 >
// //                   <MessageSquare className="w-6 h-6" />
// //                   <span>AI Assistant</span>
// //                 </Button>
// //               </div>
// //             </Card>

// //             {/* Upcoming Tasks */}
// //             <Card className="p-6 border-border bg-card">
// //               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Upcoming Tasks</h3>
// //               <div className="space-y-3">
// //                 {tasks.map((task) => (
// //                   <div
// //                     key={task.id}
// //                     className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
// //                   >
// //                     <div className="flex items-start gap-3">
// //                       <input
// //                         type="checkbox"
// //                         className="mt-1 w-4 h-4 rounded border-border"
// //                       />
// //                       <div className="flex-1">
// //                         <p className="font-['Inter'] font-medium">{task.task}</p>
// //                         <div className="flex items-center gap-2 mt-1">
// //                           <p className="text-xs text-muted-foreground">
// //                             {format(parseISO(task.date), "MMM d")} at {task.time}
// //                           </p>
// //                         </div>
// //                       </div>
// //                     </div>
// //                   </div>
// //                 ))}
// //               </div>
// //             </Card>
// //           </div>
// //         </main>
// //       </div>

// //       {/* Modals */}
// //       {activeModal === "transaction" && <TransactionModal />}
// //       {activeModal === "task" && <TaskModal />}
// //     </div>
// //   );
// // }

// import { useEffect, useState } from "react";
// import { Button } from "./ui/button";
// import { Card } from "./ui/card";
// import { ThemeToggle } from "./ThemeToggle";
// import {
//   LayoutDashboard,
//   CreditCard,
//   MessageSquare,
//   Settings,
//   Plus,
//   TrendingUp,
//   TrendingDown,
//   Wallet,
//   Target,
//   ArrowUpRight,
//   ArrowDownRight,
//   MoreVertical,
//   ShieldCheck,
// } from "lucide-react";
// import { Badge } from "./ui/badge";
// import { Progress } from "./ui/progress";
// import {
//   PieChart,
//   Pie,
//   Cell,
//   LineChart,
//   Line,
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Legend,
// } from "recharts";
// import {
//   parseISO,
//   format,
//   subDays,
//   eachDayOfInterval,
//   startOfDay,
//   endOfDay,
//   isWithinInterval,
// } from "date-fns";

// interface DashboardProps {
//   onNavigate: (page: string) => void;
// }

// interface Task {
//   id: number;
//   task: string;
//   date: string;
//   time: string;
// }

// interface BackendTransaction {
//   id: number;
//   description: string;
//   amount: number;
//   date: string;
//   category?: string;
//   ml_confidence?: number;
// }

// interface Transaction {
//   id: number;
//   name: string;
//   category?: string;
//   amount: number;
//   date: string;
//   rawDate: string;
//   icon?: string;
// }

// interface TransactionFormData {
//   description: string;
//   amount: string;
//   date: string;
//   time: string;
// }

// interface TaskFormData {
//   task: string;
//   date: string;
//   time: string;
// }

// export function Dashboard({ onNavigate }: DashboardProps) {
//   const [activeModal, setActiveModal] = useState<string | null>(null);
//   const [tasks, setTasks] = useState<Task[]>([]);
//   const [transactions, setTransactions] = useState<Transaction[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);

//   // Derived / computed UI state
//   const [totalBalance, setTotalBalance] = useState<number>(0);
//   const [totalIncome, setTotalIncome] = useState<number>(0);
//   const [totalExpenses, setTotalExpenses] = useState<number>(0);
//   const [savingsProgress, setSavingsProgress] = useState<number>(0);
//   const [weeklyBalance, setWeeklyBalance] = useState<Array<{ day: string; balance: number }>>([]);
//   const [categorySpending, setCategorySpending] = useState<Array<{ category: string; amount: number }>>([]);
//   const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
//   const [pieData, setPieData] = useState<Array<{ name: string; value: number; color?: string }>>([]);

//   const COLORS = ["#4A90E2", "#50E3C2", "#F5A623", "#9B59B6", "#E74C3C", "#7F8C8D"];

//   // Transaction Modal Component
//   const TransactionModal = () => {
//     const [formData, setFormData] = useState<TransactionFormData>({
//       description: '',
//       amount: '',
//       date: new Date().toISOString().split('T')[0],
//       time: new Date().toTimeString().slice(0, 5),
//     });
//     const [submitting, setSubmitting] = useState(false);
//     const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

//     const handleSubmit = async (e: React.FormEvent) => {
//       e.preventDefault();
//       setSubmitting(true);
//       setMessage(null);

//       try {
//         const token = localStorage.getItem("token");
//         if (!token) {
//           throw new Error("No authentication token found");
//         }

//         // Format date to match backend expectation: "YYYY-MM-DD HH:MM"
//         const dateTime = `${formData.date} ${formData.time}`;

//         const transactionData = {
//           description: formData.description,
//           amount: parseFloat(formData.amount),
//           date: dateTime, // Now in "YYYY-MM-DD HH:MM" format
//         };

//         console.log("Sending transaction data:", transactionData);

//         const response = await fetch("http://127.0.0.1:5000/transactions/add", {
//           method: "POST",
//           headers: {
//             "Content-Type": "application/json",
//             "Authorization": `Bearer ${token}`,
//           },
//           body: JSON.stringify(transactionData),
//         });

//         if (!response.ok) {
//           const errorText = await response.text();
//           throw new Error(`Failed to add transaction: ${response.status} ${errorText}`);
//         }

//         const result = await response.json();

//         setMessage({
//           type: 'success',
//           text: `Transaction added successfully! Category: ${result.transaction_category} (${(result.transaction_confidence * 100).toFixed(1)}% confidence)`
//         });

//         // Reset form
//         setFormData({
//           description: '',
//           amount: '',
//           date: new Date().toISOString().split('T')[0],
//           time: new Date().toTimeString().slice(0, 5),
//         });

//         // Refresh transactions data
//         setTimeout(() => {
//           window.location.reload();
//         }, 2000);

//       } catch (err: any) {
//         console.error("Error adding transaction:", err);
//         setMessage({
//           type: 'error',
//           text: err.message || "Failed to add transaction"
//         });
//       } finally {
//         setSubmitting(false);
//       }
//     };

//     const handleChange = (field: keyof TransactionFormData, value: string) => {
//       setFormData(prev => ({
//         ...prev,
//         [field]: value
//       }));
//     };

//     return (
//       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
//         <div
//           className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
//           onClick={(e) => e.stopPropagation()}
//         >
//           <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
//             Add New Transaction
//           </h3>

//           <form onSubmit={handleSubmit} className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium mb-2 font-['Inter']">
//                 Description *
//               </label>
//               <input
//                 type="text"
//                 required
//                 value={formData.description}
//                 onChange={(e) => handleChange('description', e.target.value)}
//                 placeholder="e.g., Grocery shopping, Salary, etc."
//                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//               />
//             </div>

//             <div>
//               <label className="block text-sm font-medium mb-2 font-['Inter']">
//                 Amount *
//               </label>
//               <input
//                 type="number"
//                 step="0.01"
//                 required
//                 value={formData.amount}
//                 onChange={(e) => handleChange('amount', e.target.value)}
//                 placeholder="0.00"
//                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//               />
//               <p className="text-xs text-muted-foreground mt-1">
//                 Use positive for income, negative for expenses (e.g., -50.00)
//               </p>
//             </div>

//             <div className="grid grid-cols-2 gap-4">
//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Date
//                 </label>
//                 <input
//                   type="date"
//                   value={formData.date}
//                   onChange={(e) => handleChange('date', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Time
//                 </label>
//                 <input
//                   type="time"
//                   value={formData.time}
//                   onChange={(e) => handleChange('time', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>
//             </div>

//             {message && (
//               <div className={`p-3 rounded-lg ${message.type === 'success'
//                   ? 'bg-green-500/10 text-green-600 border border-green-500/20'
//                   : 'bg-red-500/10 text-red-600 border border-red-500/20'
//                 }`}>
//                 <p className="text-sm font-['Inter']">{message.text}</p>
//               </div>
//             )}

//             <div className="flex gap-3 pt-2">
//               <Button
//                 type="button"
//                 variant="outline"
//                 className="flex-1"
//                 onClick={() => setActiveModal(null)}
//                 disabled={submitting}
//               >
//                 Cancel
//               </Button>
//               <Button
//                 type="submit"
//                 className="flex-1 bg-primary hover:bg-primary/90"
//                 disabled={submitting}
//               >
//                 {submitting ? "Adding..." : "Add Transaction"}
//               </Button>
//             </div>
//           </form>
//         </div>
//       </div>
//     );
//   };

//   // Task Modal Component
//   const TaskModal = () => {
//     const [formData, setFormData] = useState<TaskFormData>({
//       task: '',
//       date: new Date().toISOString().split('T')[0],
//       time: new Date().toTimeString().slice(0, 5),
//     });
//     const [submitting, setSubmitting] = useState(false);
//     const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

//     const handleSubmit = async (e: React.FormEvent) => {
//       e.preventDefault();
//       setSubmitting(true);
//       setMessage(null);

//       try {
//         const token = localStorage.getItem("token");
//         if (!token) {
//           throw new Error("No authentication token found");
//         }

//         const taskData = {
//           task: formData.task,
//           date: formData.date,
//           time: formData.time,
//         };

//         console.log("Sending task data:", taskData);

//         const response = await fetch("http://127.0.0.1:5000/tasks", {
//           method: "POST",
//           headers: {
//             "Content-Type": "application/json",
//             "Authorization": `Bearer ${token}`,
//           },
//           body: JSON.stringify(taskData),
//         });

//         if (!response.ok) {
//           const errorText = await response.text();
//           throw new Error(`Failed to add task: ${response.status} ${errorText}`);
//         }

//         const result = await response.json();

//         setMessage({
//           type: 'success',
//           text: result.message || "Task added successfully!"
//         });

//         // Reset form
//         setFormData({
//           task: '',
//           date: new Date().toISOString().split('T')[0],
//           time: new Date().toTimeString().slice(0, 5),
//         });

//         // Refresh tasks data
//         setTimeout(() => {
//           window.location.reload();
//         }, 2000);

//       } catch (err: any) {
//         console.error("Error adding task:", err);
//         setMessage({
//           type: 'error',
//           text: err.message || "Failed to add task"
//         });
//       } finally {
//         setSubmitting(false);
//       }
//     };

//     const handleChange = (field: keyof TaskFormData, value: string) => {
//       setFormData(prev => ({
//         ...prev,
//         [field]: value
//       }));
//     };

//     return (
//       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
//         <div
//           className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
//           onClick={(e) => e.stopPropagation()}
//         >
//           <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
//             Add New Task
//           </h3>

//           <form onSubmit={handleSubmit} className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium mb-2 font-['Inter']">
//                 Task Description *
//               </label>
//               <textarea
//                 required
//                 value={formData.task}
//                 onChange={(e) => handleChange('task', e.target.value)}
//                 placeholder="e.g., Pay electricity bill, Review budget, etc."
//                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px] resize-none"
//                 rows={3}
//               />
//             </div>

//             <div className="grid grid-cols-2 gap-4">
//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Date
//                 </label>
//                 <input
//                   type="date"
//                   value={formData.date}
//                   onChange={(e) => handleChange('date', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Time
//                 </label>
//                 <input
//                   type="time"
//                   value={formData.time}
//                   onChange={(e) => handleChange('time', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>
//             </div>

//             {message && (
//               <div className={`p-3 rounded-lg ${message.type === 'success'
//                   ? 'bg-green-500/10 text-green-600 border border-green-500/20'
//                   : 'bg-red-500/10 text-red-600 border border-red-500/20'
//                 }`}>
//                 <p className="text-sm font-['Inter']">{message.text}</p>
//               </div>
//             )}

//             <div className="flex gap-3 pt-2">
//               <Button
//                 type="button"
//                 variant="outline"
//                 className="flex-1"
//                 onClick={() => setActiveModal(null)}
//                 disabled={submitting}
//               >
//                 Cancel
//               </Button>
//               <Button
//                 type="submit"
//                 className="flex-1 bg-primary hover:bg-primary/90"
//                 disabled={submitting}
//               >
//                 {submitting ? "Adding..." : "Add Task"}
//               </Button>
//             </div>
//           </form>
//         </div>
//       </div>
//     );
//   };

//   // Fetch data on component mount
//   useEffect(() => {
//     const fetchData = async () => {
//       setLoading(true);
//       setError(null);
//       try {
//         const token = localStorage.getItem("token");
//         if (!token) {
//           throw new Error("No token found in localStorage");
//         }

//         const [taskRes, transactionRes] = await Promise.all([
//           fetch("http://127.0.0.1:5000/tasks", {
//             headers: { Authorization: `Bearer ${token}` },
//           }),
//           fetch("http://127.0.0.1:5000/transactions", {
//             headers: { Authorization: `Bearer ${token}` },
//           }),
//         ]);

//         if (!taskRes.ok) {
//           const txt = await taskRes.text();
//           throw new Error(`Tasks fetch failed: ${taskRes.status} ${txt}`);
//         }
//         if (!transactionRes.ok) {
//           const txt = await transactionRes.text();
//           throw new Error(`Transactions fetch failed: ${transactionRes.status} ${txt}`);
//         }

//         const taskData = await taskRes.json();
//         const transactionData = await transactionRes.json();

//         setTasks(taskData.tasks || []);

//         const backendTransactions: BackendTransaction[] =
//           Array.isArray(transactionData) ? transactionData : transactionData.transactions || [];

//         const mapped: Transaction[] = backendTransactions.map((t) => {
//           const rawDate = t.date ?? new Date().toISOString();
//           const friendly = format(parseISO(rawDate), "PPP, p");
//           return {
//             id: t.id,
//             name: t.description || t.category || "Transaction",
//             category: t.category || "Other",
//             amount: t.amount || 0,
//             date: friendly,
//             rawDate,
//           };
//         });

//         mapped.sort((a, b) => (parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime()));
//         setTransactions(mapped);
//         computeDerivedStats(mapped);
//       } catch (err: any) {
//         console.error("Error fetching data:", err);
//         setError(err.message || "Failed to fetch data");
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchData();
//   }, []);

//   function computeDerivedStats(txns: Transaction[]) {
//     const total = txns.reduce((acc, t) => acc + (t.amount ?? 0), 0);
//     const income = txns.reduce((acc, t) => acc + (t.amount > 0 ? t.amount : 0), 0);
//     const expenses = txns.reduce((acc, t) => acc + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);

//     setTotalBalance(total);
//     setTotalIncome(income);
//     setTotalExpenses(expenses);

//     const targetSavings = Math.max(4500, income * 0.5);
//     const currentSavings = Math.max(0, income - expenses);
//     const progress = targetSavings > 0 ? Math.min(100, Math.round((currentSavings / targetSavings) * 100)) : 0;
//     setSavingsProgress(progress);

//     setRecentTransactions(txns.slice(0, 5));

//     const catMap = new Map<string, number>();
//     for (const t of txns) {
//       const cat = t.category || "Other";
//       const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
//       catMap.set(cat, (catMap.get(cat) || 0) + amt);
//     }
//     const categoryArr = Array.from(catMap.entries()).map(([category, amount]) => ({ category, amount }));
//     categoryArr.sort((a, b) => b.amount - a.amount);
//     setCategorySpending(categoryArr);

//     const pie = categoryArr.slice(0, 6).map((c, i) => ({
//       name: c.category,
//       value: c.amount,
//       color: COLORS[i % COLORS.length],
//     }));
//     if (pie.length === 0) {
//       setPieData([{ name: "Other", value: 1, color: COLORS[0] }]);
//     } else {
//       setPieData(pie);
//     }

//     const today = new Date();
//     const days = eachDayOfInterval({ start: subDays(startOfDay(today), 6), end: startOfDay(today) });
//     const ascTxns = [...txns].sort((a, b) => parseISO(a.rawDate).getTime() - parseISO(b.rawDate).getTime());
//     const balances: { day: string; balance: number }[] = [];

//     for (const day of days) {
//       const dayStart = startOfDay(day);
//       const dayEnd = endOfDay(day);
//       const cumulative = ascTxns
//         .filter((t) => parseISO(t.rawDate) <= dayEnd)
//         .reduce((acc, t) => acc + (t.amount ?? 0), 0);

//       balances.push({
//         day: format(day, "EEE"),
//         balance: Math.round(cumulative * 100) / 100,
//       });
//     }

//     setWeeklyBalance(balances);
//   }

//   if (loading) {
//     return (
//       <div className="min-h-screen flex items-center justify-center">
//         <p>Loading dashboard...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="min-h-screen flex items-center justify-center">
//         <p>Error loading dashboard: {error}</p>
//       </div>
//     );
//   }

//   return (
//     <div className="min-h-screen bg-background">
//       {/* Sidebar */}
//       <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border p-6 hidden lg:block">
//         <div className="flex items-center gap-2 mb-8">
//           <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
//             <Wallet className="w-6 h-6 text-white" />
//           </div>
//           <h1 className="font-['Poppins'] font-bold text-xl">Ohmatt</h1>
//         </div>

//         <nav className="space-y-2">
//           <Button
//             variant="default"
//             className="w-full justify-start gap-3 bg-primary text-primary-foreground"
//           >
//             <LayoutDashboard className="w-5 h-5" />
//             Dashboard
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("transactions")}
//           >
//             <CreditCard className="w-5 h-5" />
//             Transactions
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("messages")}
//           >
//             <MessageSquare className="w-5 h-5" />
//             Messages
//             <Badge className="ml-auto bg-accent">3</Badge>
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("settings")}
//           >
//             <Settings className="w-5 h-5" />
//             Settings
//           </Button>
//         </nav>

//         <div className="mt-8 p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg border border-primary/20">
//           <ShieldCheck className="w-8 h-8 text-primary mb-2" />
//           <h4 className="font-['Poppins'] font-semibold mb-1">Pro Features</h4>
//           <p className="text-sm text-muted-foreground mb-3 font-['Inter']">
//             Unlock advanced analytics and insights
//           </p>
//           <Button size="sm" className="w-full bg-primary">
//             Upgrade Now
//           </Button>
//         </div>
//       </aside>

//       {/* Main Content */}
//       <div className="lg:ml-64">
//         {/* Header */}
//         <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
//           <div className="px-4 sm:px-6 lg:px-8 py-4">
//             <div className="flex items-center justify-between">
//               <div>
//                 <h2 className="font-['Poppins'] font-bold text-2xl">Dashboard</h2>
//                 <p className="text-muted-foreground font-['Inter']">
//                   Welcome back! Here's your financial overview.
//                 </p>
//               </div>
//               <div className="flex items-center gap-3">
//                 <ThemeToggle />
//                 <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
//                   <span className="text-white font-['Inter'] font-semibold">JD</span>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </header>

//         {/* Content */}
//         <main className="p-4 sm:p-6 lg:p-8">
//           {/* Stats Cards */}
//           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
//             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
//               <div className="flex items-center justify-between mb-4">
//                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
//                   <Wallet className="w-6 h-6 text-primary" />
//                 </div>
//                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
//                   <TrendingUp className="w-3 h-3 mr-1" />
//                   +12.5%
//                 </Badge>
//               </div>
//               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
//                 Total Balance
//               </p>
//               <h3 className="font-['Poppins'] font-bold text-2xl">${totalBalance.toFixed(2)}</h3>
//             </Card>

//             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
//               <div className="flex items-center justify-between mb-4">
//                 <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
//                   <ArrowUpRight className="w-6 h-6 text-secondary" />
//                 </div>
//                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
//                   <TrendingUp className="w-3 h-3 mr-1" />
//                   +8.2%
//                 </Badge>
//               </div>
//               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
//                 Total Income
//               </p>
//               <h3 className="font-['Poppins'] font-bold text-2xl">${totalIncome.toFixed(2)}</h3>
//             </Card>

//             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
//               <div className="flex items-center justify-between mb-4">
//                 <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
//                   <ArrowDownRight className="w-6 h-6 text-accent" />
//                 </div>
//                 <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
//                   <TrendingDown className="w-3 h-3 mr-1" />
//                   -5.1%
//                 </Badge>
//               </div>
//               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
//                 Total Expenses
//               </p>
//               <h3 className="font-['Poppins'] font-bold text-2xl">${totalExpenses.toFixed(2)}</h3>
//             </Card>

//             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
//               <div className="flex items-center justify-between mb-4">
//                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
//                   <Target className="w-6 h-6 text-primary" />
//                 </div>
//                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
//                   {savingsProgress}%
//                 </Badge>
//               </div>
//               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
//                 Savings Goal
//               </p>
//               <h3 className="font-['Poppins'] font-bold text-2xl">${(totalIncome * 0.5).toFixed(0)}</h3>
//             </Card>
//           </div>

//           {/* Charts Section */}
//           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
//             {/* Monthly Expenses Chart */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Monthly Expenses
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Breakdown by category
//                   </p>
//                 </div>
//                 <Button variant="ghost" size="icon">
//                   <MoreVertical className="w-4 h-4" />
//                 </Button>
//               </div>
//               <ResponsiveContainer width="100%" height={280}>
//                 <PieChart>
//                   <Pie
//                     data={pieData}
//                     cx="50%"
//                     cy="50%"
//                     innerRadius={60}
//                     outerRadius={100}
//                     paddingAngle={5}
//                     dataKey="value"
//                   >
//                     {pieData.map((entry, index) => (
//                       <Cell key={`cell-${index}`} fill={entry.color} />
//                     ))}
//                   </Pie>
//                   <Tooltip />
//                   <Legend />
//                 </PieChart>
//               </ResponsiveContainer>
//             </Card>

//             {/* Weekly Balance Chart */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Weekly Balance
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Balance trend over the week
//                   </p>
//                 </div>
//                 <Button variant="ghost" size="icon">
//                   <MoreVertical className="w-4 h-4" />
//                 </Button>
//               </div>
//               <ResponsiveContainer width="100%" height={280}>
//                 <LineChart data={weeklyBalance}>
//                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
//                   <XAxis dataKey="day" stroke="var(--color-muted-foreground)" />
//                   <YAxis stroke="var(--color-muted-foreground)" />
//                   <Tooltip
//                     contentStyle={{
//                       backgroundColor: "var(--color-card)",
//                       border: "1px solid var(--color-border)",
//                       borderRadius: "8px",
//                     }}
//                   />
//                   <Line
//                     type="monotone"
//                     dataKey="balance"
//                     stroke="#4A90E2"
//                     strokeWidth={3}
//                     dot={{ fill: "#4A90E2", r: 5 }}
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </Card>

//             {/* Category Spending Chart */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Category Spending
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Top spending categories
//                   </p>
//                 </div>
//                 <Button variant="ghost" size="icon">
//                   <MoreVertical className="w-4 h-4" />
//                 </Button>
//               </div>
//               <ResponsiveContainer width="100%" height={280}>
//                 <BarChart data={categorySpending}>
//                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
//                   <XAxis dataKey="category" stroke="var(--color-muted-foreground)" />
//                   <YAxis stroke="var(--color-muted-foreground)" />
//                   <Tooltip
//                     contentStyle={{
//                       backgroundColor: "var(--color-card)",
//                       border: "1px solid var(--color-border)",
//                       borderRadius: "8px",
//                     }}
//                   />
//                   <Bar dataKey="amount" fill="#4A90E2" radius={[8, 8, 0, 0]} />
//                 </BarChart>
//               </ResponsiveContainer>
//             </Card>

//             {/* Recent Transactions */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Recent Transactions
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Latest activity
//                   </p>
//                 </div>
//                 <Button
//                   variant="ghost"
//                   size="sm"
//                   onClick={() => onNavigate("transactions")}
//                 >
//                   View All
//                 </Button>
//               </div>
//               <div className="space-y-4">
//                 {recentTransactions.map((transaction) => (
//                   <div
//                     key={transaction.id}
//                     className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
//                   >
//                     <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-xl">
//                       {transaction.icon}
//                     </div>
//                     <div className="flex-1 min-w-0">
//                       <p className="font-['Inter'] font-medium truncate">
//                         {transaction.name}
//                       </p>
//                       <p className="text-sm text-muted-foreground font-['Inter']">
//                         {transaction.date}
//                       </p>
//                     </div>
//                     <div
//                       className={`font-['Inter'] font-semibold ${transaction.amount > 0 ? "text-secondary" : "text-foreground"
//                         }`}
//                     >
//                       {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </Card>
//           </div>

//           {/* Quick Actions & Tasks */}
//           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//             {/* Quick Actions */}
//             <Card className="p-6 border-border bg-card lg:col-span-2">
//               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Quick Actions</h3>
//               <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-primary hover:bg-primary/90 shadow-md hover:shadow-lg transition-all"
//                   onClick={() => setActiveModal("transaction")}
//                 >
//                   <Plus className="w-6 h-6" />
//                   <span>Add Transaction</span>
//                 </Button>
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-secondary hover:bg-secondary/90 text-secondary-foreground shadow-md hover:shadow-lg transition-all"
//                   onClick={() => setActiveModal("task")}
//                 >
//                   <Plus className="w-6 h-6" />
//                   <span>Add Task</span>
//                 </Button>
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-accent hover:bg-accent/90 shadow-md hover:shadow-lg transition-all"
//                   onClick={() => onNavigate("messages")}
//                 >
//                   <MessageSquare className="w-6 h-6" />
//                   <span>AI Assistant</span>
//                 </Button>
//                 <Button
//                   variant="ghost"
//                   className="w-full justify-start gap-3"
//                   onClick={() => onNavigate("bank-connection")}
//                 >
//                   <Banknote className="w-5 h-5" />
//                   Bank Connections
//                 </Button>
//               </div>
//             </Card>

//             {/* Upcoming Tasks */}
//             <Card className="p-6 border-border bg-card">
//               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Upcoming Tasks</h3>
//               <div className="space-y-3">
//                 {tasks.map((task) => (
//                   <div
//                     key={task.id}
//                     className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
//                   >
//                     <div className="flex items-start gap-3">
//                       <input
//                         type="checkbox"
//                         className="mt-1 w-4 h-4 rounded border-border"
//                       />
//                       <div className="flex-1">
//                         <p className="font-['Inter'] font-medium">{task.task}</p>
//                         <div className="flex items-center gap-2 mt-1">
//                           <p className="text-xs text-muted-foreground">
//                             {format(parseISO(task.date), "MMM d")} at {task.time}
//                           </p>
//                         </div>
//                       </div>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </Card>
//           </div>
//         </main>
//       </div>

//       {/* Modals */}
//       {activeModal === "transaction" && <TransactionModal />}
//       {activeModal === "task" && <TaskModal />}
//     </div>
//   );
// }

import { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { ThemeToggle } from "./ThemeToggle";
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
  Banknote, // Added Banknote icon
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  parseISO,
  format,
  subDays,
  eachDayOfInterval,
  startOfDay,
  endOfDay,
  isWithinInterval,
} from "date-fns";

interface DashboardProps {
  onNavigate: (page: string) => void;
}

interface Task {
  id: number;
  task: string;
  date: string;
  time: string;
}

interface BackendTransaction {
  id: number;
  description: string;
  amount: number;
  date: string;
  category?: string;
  ml_confidence?: number;
}

interface Transaction {
  id: number;
  name: string;
  category?: string;
  amount: number;
  date: string;
  rawDate: string;
  icon?: string;
}

interface TransactionFormData {
  description: string;
  amount: string;
  date: string;
  time: string;
}

interface TaskFormData {
  task: string;
  date: string;
  time: string;
}

interface BankAccount {
  id: number;
  institution_name: string;
  account_name: string;
  account_type: string;
  balance_available: number;
  balance_current: number;
  currency: string;
}

interface BankTransaction {
  id: number;
  description: string;
  amount: number;
  date: string;
  category: string;
  merchant_name: string;
  pending: boolean;
  account_name: string;
}

// NEW: Interface for user profile data from backend
interface UserProfile {
  user: string; // This is the username from your backend
  tasks?: any[];
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [bankTransactions, setBankTransactions] = useState<BankTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Combined financial data state
  const [totalBalance, setTotalBalance] = useState<number>(0);
  const [totalIncome, setTotalIncome] = useState<number>(0);
  const [totalExpenses, setTotalExpenses] = useState<number>(0);
  const [savingsProgress, setSavingsProgress] = useState<number>(0);
  const [weeklyBalance, setWeeklyBalance] = useState<Array<{ day: string; balance: number }>>([]);
  const [categorySpending, setCategorySpending] = useState<Array<{ category: string; amount: number }>>([]);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [pieData, setPieData] = useState<Array<{ name: string; value: number; color?: string }>>([]);

  const COLORS = ["#4A90E2", "#50E3C2", "#F5A623", "#9B59B6", "#E74C3C", "#7F8C8D"];

  // Transaction Modal Component
  const TransactionModal = () => {
    const [formData, setFormData] = useState<TransactionFormData>({
      description: '',
      amount: '',
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().slice(0, 5),
    });
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);
      setMessage(null);

      try {
        const token = localStorage.getItem("token");
        if (!token) {
          throw new Error("No authentication token found");
        }

        // Format date to match backend expectation: "YYYY-MM-DD HH:MM"
        const dateTime = `${formData.date} ${formData.time}`;

        const transactionData = {
          description: formData.description,
          amount: parseFloat(formData.amount),
          date: dateTime,
        };

        console.log("Sending transaction data:", transactionData);

        const response = await fetch("http://127.0.0.1:5000/transactions/add", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify(transactionData),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to add transaction: ${response.status} ${errorText}`);
        }

        const result = await response.json();

        setMessage({
          type: 'success',
          text: `Transaction added successfully! Category: ${result.transaction_category} (${(result.transaction_confidence * 100).toFixed(1)}% confidence)`
        });

        // Reset form
        setFormData({
          description: '',
          amount: '',
          date: new Date().toISOString().split('T')[0],
          time: new Date().toTimeString().slice(0, 5),
        });

        // Refresh all data
        setTimeout(() => {
          fetchCombinedData();
        }, 2000);

      } catch (err: any) {
        console.error("Error adding transaction:", err);
        setMessage({
          type: 'error',
          text: err.message || "Failed to add transaction"
        });
      } finally {
        setSubmitting(false);
      }
    };

    const handleChange = (field: keyof TransactionFormData, value: string) => {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    };

    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div
          className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
            Add New Transaction
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 font-['Inter']">
                Description *
              </label>
              <input
                type="text"
                required
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="e.g., Grocery shopping, Salary, etc."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 font-['Inter']">
                Amount *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.amount}
                onChange={(e) => handleChange('amount', e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use positive for income, negative for expenses (e.g., -50.00)
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 font-['Inter']">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 font-['Inter']">
                  Time
                </label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => handleChange('time', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            {message && (
              <div className={`p-3 rounded-lg ${message.type === 'success'
                ? 'bg-green-500/10 text-green-600 border border-green-500/20'
                : 'bg-red-500/10 text-red-600 border border-red-500/20'
                }`}>
                <p className="text-sm font-['Inter']">{message.text}</p>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => setActiveModal(null)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-primary hover:bg-primary/90"
                disabled={submitting}
              >
                {submitting ? "Adding..." : "Add Transaction"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Task Modal Component
  const TaskModal = () => {
    const [formData, setFormData] = useState<TaskFormData>({
      task: '',
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().slice(0, 5),
    });
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);
      setMessage(null);

      try {
        const token = localStorage.getItem("token");
        if (!token) {
          throw new Error("No authentication token found");
        }

        const taskData = {
          task: formData.task,
          date: formData.date,
          time: formData.time,
        };

        console.log("Sending task data:", taskData);

        const response = await fetch("http://127.0.0.1:5000/tasks", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify(taskData),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to add task: ${response.status} ${errorText}`);
        }

        const result = await response.json();

        setMessage({
          type: 'success',
          text: result.message || "Task added successfully!"
        });

        // Reset form
        setFormData({
          task: '',
          date: new Date().toISOString().split('T')[0],
          time: new Date().toTimeString().slice(0, 5),
        });

        // Refresh tasks data
        setTimeout(() => {
          fetchCombinedData();
        }, 2000);

      } catch (err: any) {
        console.error("Error adding task:", err);
        setMessage({
          type: 'error',
          text: err.message || "Failed to add task"
        });
      } finally {
        setSubmitting(false);
      }
    };

    const handleChange = (field: keyof TaskFormData, value: string) => {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    };

    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div
          className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
            Add New Task
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 font-['Inter']">
                Task Description *
              </label>
              <textarea
                required
                value={formData.task}
                onChange={(e) => handleChange('task', e.target.value)}
                placeholder="e.g., Pay electricity bill, Review budget, etc."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px] resize-none"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 font-['Inter']">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 font-['Inter']">
                  Time
                </label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => handleChange('time', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            {message && (
              <div className={`p-3 rounded-lg ${message.type === 'success'
                ? 'bg-green-500/10 text-green-600 border border-green-500/20'
                : 'bg-red-500/10 text-red-600 border border-red-500/20'
                }`}>
                <p className="text-sm font-['Inter']">{message.text}</p>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => setActiveModal(null)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-primary hover:bg-primary/90"
                disabled={submitting}
              >
                {submitting ? "Adding..." : "Add Task"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Fetch combined data (manual transactions + bank data)
  const fetchCombinedData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("No token found in localStorage");
      }

      // Fetch all data sources in parallel
      const [taskRes, transactionRes, bankAccountsRes, bankTransactionsRes] = await Promise.all([
        fetch("http://127.0.0.1:5000/simple-tasks", {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => {
          console.log("Tasks endpoint failed, using fallback");
          return new Response(JSON.stringify({ tasks: [] }));
        }),
        // fetch("http://127.0.0.1:5000/tasks", {
        //   headers: { Authorization: `Bearer ${token}` },
        // }).catch(() => {
        //   console.log("Tasks endpoint failed, using fallback");
        //   return new Response(JSON.stringify({ tasks: [] }));
        // }),
        fetch("http://127.0.0.1:5000/transactions", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("http://127.0.0.1:5000/bank/accounts", {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => new Response(JSON.stringify([]))),
        fetch("http://127.0.0.1:5000/bank/transactions?days=30", {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => new Response(JSON.stringify([]))),
      ]);

      // Handle tasks
      let tasksData = { tasks: [] };
      if (taskRes.ok) {
        try {
          tasksData = await taskRes.json();
        } catch (e) {
          console.log("Failed to parse tasks response, using fallback");
        }
      }
      setTasks(tasksData.tasks || []);

      // Handle manual transactions
      let manualTransactions: Transaction[] = [];
      if (transactionRes.ok) {
        const transactionData = await transactionRes.json();
        const backendTransactions: BackendTransaction[] =
          Array.isArray(transactionData) ? transactionData : transactionData.transactions || [];

        manualTransactions = backendTransactions.map((t) => {
          const rawDate = t.date ?? new Date().toISOString();
          const friendly = format(parseISO(rawDate), "PPP, p");
          return {
            id: t.id,
            name: t.description || t.category || "Transaction",
            category: t.category || "Other",
            amount: t.amount || 0,
            date: friendly,
            rawDate,
          };
        });

        manualTransactions.sort((a, b) => (parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime()));
        setTransactions(manualTransactions);
      }

      // Handle bank accounts
      let bankAccountsData: BankAccount[] = [];
      if (bankAccountsRes.ok) {
        bankAccountsData = await bankAccountsRes.json();
        setBankAccounts(bankAccountsData);
      }

      // Handle bank transactions
      let bankTransactionsData: BankTransaction[] = [];
      if (bankTransactionsRes.ok) {
        bankTransactionsData = await bankTransactionsRes.json();
        setBankTransactions(bankTransactionsData);
      }

      // Compute combined financial data
      computeCombinedFinancialData(manualTransactions, bankAccountsData, bankTransactionsData);

    } catch (err: any) {
      console.error("Error fetching data:", err);
      setError(err.message || "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  // Compute combined financial data from all sources
  const computeCombinedFinancialData = (
    manualTxns: Transaction[],
    bankAccounts: BankAccount[],
    bankTxns: BankTransaction[]
  ) => {
    // Calculate totals from bank accounts
    const bankBalance = bankAccounts.reduce((sum, account) => sum + account.balance_current, 0);

    // Calculate totals from manual transactions
    const manualIncome = manualTxns.reduce((sum, t) => sum + (t.amount > 0 ? t.amount : 0), 0);
    const manualExpenses = manualTxns.reduce((sum, t) => sum + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);
    const manualNet = manualIncome - manualExpenses;

    // Calculate totals from bank transactions
    const bankIncome = bankTxns.reduce((sum, t) => sum + (t.amount > 0 ? t.amount : 0), 0);
    const bankExpenses = bankTxns.reduce((sum, t) => sum + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);

    // Combined totals
    const combinedBalance = bankBalance + manualNet;
    const combinedIncome = manualIncome + bankIncome;
    const combinedExpenses = manualExpenses + bankExpenses;

    setTotalBalance(combinedBalance);
    setTotalIncome(combinedIncome);
    setTotalExpenses(combinedExpenses);

    // Savings progress
    const targetSavings = Math.max(4500, combinedIncome * 0.5);
    const currentSavings = Math.max(0, combinedIncome - combinedExpenses);
    const progress = targetSavings > 0 ? Math.min(100, Math.round((currentSavings / targetSavings) * 100)) : 0;
    setSavingsProgress(progress);

    // Combine recent transactions (manual + bank)
    const allTransactions: Transaction[] = [
      ...manualTxns,
      ...bankTxns.map(t => ({
        id: t.id,
        name: t.description,
        category: t.category,
        amount: t.amount,
        date: format(parseISO(t.date), "PPP, p"),
        rawDate: t.date,
        icon: "🏦" // Bank icon for bank transactions
      }))
    ].sort((a, b) => parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime())
      .slice(0, 5);

    setRecentTransactions(allTransactions);

    // Category spending (from both manual and bank transactions)
    const catMap = new Map<string, number>();

    // Add manual transactions
    for (const t of manualTxns) {
      const cat = t.category || "Other";
      const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
      catMap.set(cat, (catMap.get(cat) || 0) + amt);
    }

    // Add bank transactions
    for (const t of bankTxns) {
      const cat = t.category || "Other";
      const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
      catMap.set(cat, (catMap.get(cat) || 0) + amt);
    }

    const categoryArr = Array.from(catMap.entries()).map(([category, amount]) => ({ category, amount }));
    categoryArr.sort((a, b) => b.amount - a.amount);
    setCategorySpending(categoryArr);

    // Pie data
    const pie = categoryArr.slice(0, 6).map((c, i) => ({
      name: c.category,
      value: c.amount,
      color: COLORS[i % COLORS.length],
    }));
    if (pie.length === 0) {
      setPieData([{ name: "Other", value: 1, color: COLORS[0] }]);
    } else {
      setPieData(pie);
    }

    // Weekly balance (using manual transactions for now)
    const today = new Date();
    const days = eachDayOfInterval({ start: subDays(startOfDay(today), 6), end: startOfDay(today) });
    const ascTxns = [...manualTxns].sort((a, b) => parseISO(a.rawDate).getTime() - parseISO(b.rawDate).getTime());
    const balances: { day: string; balance: number }[] = [];

    for (const day of days) {
      const dayStart = startOfDay(day);
      const dayEnd = endOfDay(day);
      const cumulative = ascTxns
        .filter((t) => parseISO(t.rawDate) <= dayEnd)
        .reduce((acc, t) => acc + (t.amount ?? 0), 0);

      balances.push({
        day: format(day, "EEE"),
        balance: Math.round(cumulative * 100) / 100,
      });
    }

    setWeeklyBalance(balances);
  };

  // Add this function to extract initials from username
const getInitials = (username: string) => {
  if (!username) return 'GHOST'; // fallback
  
  const parts = username.split(' ');
  if (parts.length === 1) {
    // Only one name, take first 2 letters
    return parts[0].substring(0, 2).toUpperCase();
  } else {
    // First letter of first name + first letter of last name
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
  }
};

// Add user state to store the user profile
const [user, setUser] = useState<{ username: string; email: string } | null>(null);

// Add this function to fetch user profile
const fetchUserProfile = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) return;

    const response = await fetch("http://127.0.0.1:5000/profile", { // Adjust endpoint as needed
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });

    if (response.ok) {
      const userData = await response.json();
      setUser(userData);
    }
  } catch (err) {
    console.error("Error fetching user profile:", err);
  }
};

  // Fetch data on component mount
  useEffect(() => {
    fetchCombinedData();
    fetchUserProfile();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Error loading dashboard: {error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border p-6 hidden lg:block">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
            <Wallet className="w-6 h-6 text-white" />
          </div>
          <h1 className="font-['Poppins'] font-bold text-xl">Ohmatt</h1>
        </div>

        <nav className="space-y-2">
          <Button
            variant="default"
            className="w-full justify-start gap-3 bg-primary text-primary-foreground"
          >
            <LayoutDashboard className="w-5 h-5" />
            Dashboard
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3"
            onClick={() => onNavigate("transactions")}
          >
            <CreditCard className="w-5 h-5" />
            Transactions
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3"
            onClick={() => onNavigate("bank-connection")}
          >
            <Banknote className="w-5 h-5" />
            Bank Connections
            {bankAccounts.length > 0 && (
              <Badge className="ml-auto bg-green-500/10 text-green-600 border-green-500/20">
                {bankAccounts.length}
              </Badge>
            )}
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3"
            onClick={() => onNavigate("messages")}
          >
            <MessageSquare className="w-5 h-5" />
            Messages
            <Badge className="ml-auto bg-accent">3</Badge>
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3"
            onClick={() => onNavigate("settings")}
          >
            <Settings className="w-5 h-5" />
            Settings
          </Button>
        </nav>

        <div className="mt-8 p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg border border-primary/20">
          <ShieldCheck className="w-8 h-8 text-primary mb-2" />
          <h4 className="font-['Poppins'] font-semibold mb-1">Pro Features</h4>
          <p className="text-sm text-muted-foreground mb-3 font-['Inter']">
            Unlock advanced analytics and insights
          </p>
          <Button size="sm" className="w-full bg-primary">
            Upgrade Now
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-['Poppins'] font-bold text-2xl">Dashboard</h2>
                <p className="text-muted-foreground font-['Inter']">
                  Welcome back! Here's your financial overview.
                  {bankAccounts.length > 0 && (
                    <span className="text-green-600 ml-2">
                      • {bankAccounts.length} bank account{bankAccounts.length > 1 ? 's' : ''} connected
                    </span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
                  <span className="text-white font-['Inter'] font-semibold">{user ? getInitials(user.username) : 'GHOST'}</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-primary" />
                </div>
                <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +12.5%
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
                Total Balance
              </p>
              <h3 className="font-['Poppins'] font-bold text-2xl">${totalBalance.toFixed(2)}</h3>
              {bankAccounts.length > 0 && (
                <p className="text-xs text-green-600 mt-1">
                  Includes {bankAccounts.length} bank account{bankAccounts.length > 1 ? 's' : ''}
                </p>
              )}
            </Card>

            <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
                  <ArrowUpRight className="w-6 h-6 text-secondary" />
                </div>
                <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +8.2%
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
                Total Income
              </p>
              <h3 className="font-['Poppins'] font-bold text-2xl">${totalIncome.toFixed(2)}</h3>
            </Card>

            <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
                  <ArrowDownRight className="w-6 h-6 text-accent" />
                </div>
                <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
                  <TrendingDown className="w-3 h-3 mr-1" />
                  -5.1%
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
                Total Expenses
              </p>
              <h3 className="font-['Poppins'] font-bold text-2xl">${totalExpenses.toFixed(2)}</h3>
            </Card>

            <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Target className="w-6 h-6 text-primary" />
                </div>
                <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                  {savingsProgress}%
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
                Savings Goal
              </p>
              <h3 className="font-['Poppins'] font-bold text-2xl">${(totalIncome * 0.5).toFixed(0)}</h3>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Monthly Expenses Chart */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
                    Monthly Expenses
                  </h3>
                  <p className="text-sm text-muted-foreground font-['Inter']">
                    Breakdown by category
                  </p>
                </div>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
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
            </Card>

            {/* Weekly Balance Chart */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
                    Weekly Balance
                  </h3>
                  <p className="text-sm text-muted-foreground font-['Inter']">
                    Balance trend over the week
                  </p>
                </div>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={weeklyBalance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="day" stroke="var(--color-muted-foreground)" />
                  <YAxis stroke="var(--color-muted-foreground)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "8px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="balance"
                    stroke="#4A90E2"
                    strokeWidth={3}
                    dot={{ fill: "#4A90E2", r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>

            {/* Category Spending Chart */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
                    Category Spending
                  </h3>
                  <p className="text-sm text-muted-foreground font-['Inter']">
                    Top spending categories
                  </p>
                </div>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={categorySpending}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="category" stroke="var(--color-muted-foreground)" />
                  <YAxis stroke="var(--color-muted-foreground)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="amount" fill="#4A90E2" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            {/* Recent Transactions */}
            <Card className="p-6 border-border bg-card">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
                    Recent Transactions
                  </h3>
                  <p className="text-sm text-muted-foreground font-['Inter']">
                    Latest activity
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onNavigate("transactions")}
                >
                  View All
                </Button>
              </div>
              <div className="space-y-4">
                {recentTransactions.map((transaction) => (
                  <div
                    key={transaction.id}
                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                  >
                    <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-xl">
                      {transaction.icon || "💳"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-['Inter'] font-medium truncate">
                        {transaction.name}
                      </p>
                      <p className="text-sm text-muted-foreground font-['Inter']">
                        {transaction.date}
                      </p>
                    </div>
                    <div
                      className={`font-['Inter'] font-semibold ${transaction.amount > 0 ? "text-secondary" : "text-foreground"
                        }`}
                    >
                      {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Quick Actions & Tasks */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <Card className="p-6 border-border bg-card lg:col-span-2">
              <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Button
                  className="h-auto py-6 flex-col gap-2 bg-primary hover:bg-primary/90 shadow-md hover:shadow-lg transition-all"
                  onClick={() => setActiveModal("transaction")}
                >
                  <Plus className="w-6 h-6" />
                  <span>Add Transaction</span>
                </Button>
                <Button
                  className="h-auto py-6 flex-col gap-2 bg-secondary hover:bg-secondary/90 text-secondary-foreground shadow-md hover:shadow-lg transition-all"
                  onClick={() => setActiveModal("task")}
                >
                  <Plus className="w-6 h-6" />
                  <span>Add Task</span>
                </Button>
                <Button
                  className="h-auto py-6 flex-col gap-2 bg-green-600 hover:bg-green-700 shadow-md hover:shadow-lg transition-all"
                  onClick={() => onNavigate("bank-connection")}
                >
                  <Banknote className="w-6 h-6" />
                  <span>Connect Bank</span>
                </Button>
                <Button
                  className="h-auto py-6 flex-col gap-2 bg-accent hover:bg-accent/90 shadow-md hover:shadow-lg transition-all"
                  onClick={() => onNavigate("messages")}
                >
                  <MessageSquare className="w-6 h-6" />
                  <span>AI Assistant</span>
                </Button>
              </div>
            </Card>

            {/* Upcoming Tasks */}
            <Card className="p-6 border-border bg-card">
              <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Upcoming Tasks</h3>
              <div className="space-y-3">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        className="mt-1 w-4 h-4 rounded border-border"
                      />
                      <div className="flex-1">
                        <p className="font-['Inter'] font-medium">{task.task}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <p className="text-xs text-muted-foreground">
                            {format(parseISO(task.date), "MMM d")} at {task.time}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </main>
      </div>

      {/* Modals */}
      {activeModal === "transaction" && <TransactionModal />}
      {activeModal === "task" && <TaskModal />}
    </div>
  );
}

// import { useEffect, useState } from "react";
// import { Button } from "./ui/button";
// import { Card } from "./ui/card";
// import { ThemeToggle } from "./ThemeToggle";
// import {
//   LayoutDashboard,
//   CreditCard,
//   MessageSquare,
//   Settings,
//   Plus,
//   TrendingUp,
//   TrendingDown,
//   Wallet,
//   Target,
//   ArrowUpRight,
//   ArrowDownRight,
//   MoreVertical,
//   ShieldCheck,
//   Banknote,
// } from "lucide-react";
// import { Badge } from "./ui/badge";
// import { Progress } from "./ui/progress";
// import {
//   PieChart,
//   Pie,
//   Cell,
//   LineChart,
//   Line,
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   Legend,
// } from "recharts";
// import {
//   parseISO,
//   format,
//   subDays,
//   eachDayOfInterval,
//   startOfDay,
//   endOfDay,
// } from "date-fns";

// interface DashboardProps {
//   onNavigate: (page: string) => void;
// }

// interface Task {
//   id: number;
//   task: string;
//   date: string;
//   time: string;
// }

// interface BackendTransaction {
//   id: number;
//   description: string;
//   amount: number;
//   date: string;
//   category?: string;
//   ml_confidence?: number;
// }

// interface Transaction {
//   id: number;
//   name: string;
//   category?: string;
//   amount: number;
//   date: string;
//   rawDate: string;
//   icon?: string;
// }

// interface TransactionFormData {
//   description: string;
//   amount: string;
//   date: string;
//   time: string;
// }

// interface TaskFormData {
//   task: string;
//   date: string;
//   time: string;
// }

// interface BankAccount {
//   id: number;
//   institution_name: string;
//   account_name: string;
//   account_type: string;
//   balance_available: number;
//   balance_current: number;
//   currency: string;
// }

// interface BankTransaction {
//   id: number;
//   description: string;
//   amount: number;
//   date: string;
//   category: string;
//   merchant_name: string;
//   pending: boolean;
//   account_name: string;
// }

// interface UserProfile {
//   user: string; // This is the username from your backend
//   tasks?: any[];
// }

// // Add this function to extract initials from username
// const getInitials = (username: string): string => {
//   if (!username || username.trim() === '') return 'JD';
  
//   const parts = username.trim().split(' ');
  
//   if (parts.length === 1) {
//     // Only one name, take first 2 letters
//     return parts[0].substring(0, 2).toUpperCase();
//   } else {
//     // First letter of first name + first letter of last name
//     const firstName = parts[0];
//     const lastName = parts[parts.length - 1];
//     return (firstName.charAt(0) + lastName.charAt(0)).toUpperCase();
//   }
// };

// export function Dashboard({ onNavigate }: DashboardProps) {
//   const [activeModal, setActiveModal] = useState<string | null>(null);
//   const [tasks, setTasks] = useState<Task[]>([]);
//   const [transactions, setTransactions] = useState<Transaction[]>([]);
//   const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
//   const [bankTransactions, setBankTransactions] = useState<BankTransaction[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

//   // Combined financial data state
//   const [totalBalance, setTotalBalance] = useState<number>(0);
//   const [totalIncome, setTotalIncome] = useState<number>(0);
//   const [totalExpenses, setTotalExpenses] = useState<number>(0);
//   const [savingsProgress, setSavingsProgress] = useState<number>(0);
//   const [weeklyBalance, setWeeklyBalance] = useState<Array<{ day: string; balance: number }>>([]);
//   const [categorySpending, setCategorySpending] = useState<Array<{ category: string; amount: number }>>([]);
//   const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
//   const [pieData, setPieData] = useState<Array<{ name: string; value: number; color?: string }>>([]);

//   const COLORS = ["#4A90E2", "#50E3C2", "#F5A623", "#9B59B6", "#E74C3C", "#7F8C8D"];

//   // Add this function to fetch user profile
//   const fetchUserProfile = async () => {
//     try {
//       const token = localStorage.getItem("token");
//       if (!token) {
//         console.log("No token found for profile fetch");
//         return;
//       }

//       const response = await fetch("http://127.0.0.1:5000/profile", {
//         headers: {
//           "Authorization": `Bearer ${token}`,
//         },
//       });

//       if (response.ok) {
//         const userData = await response.json();
//         console.log("User profile data:", userData);
//         setUserProfile(userData);
//       } else {
//         console.log("Failed to fetch user profile:", response.status);
//       }
//     } catch (err) {
//       console.error("Error fetching user profile:", err);
//     }
//   };

//   // Transaction Modal Component
//   const TransactionModal = () => {
//     const [formData, setFormData] = useState<TransactionFormData>({
//       description: '',
//       amount: '',
//       date: new Date().toISOString().split('T')[0],
//       time: new Date().toTimeString().slice(0, 5),
//     });
//     const [submitting, setSubmitting] = useState(false);
//     const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

//     const handleSubmit = async (e: React.FormEvent) => {
//       e.preventDefault();
//       setSubmitting(true);
//       setMessage(null);

//       try {
//         const token = localStorage.getItem("token");
//         if (!token) {
//           throw new Error("No authentication token found");
//         }

//         // Format date to match backend expectation: "YYYY-MM-DD HH:MM"
//         const dateTime = `${formData.date} ${formData.time}`;

//         const transactionData = {
//           description: formData.description,
//           amount: parseFloat(formData.amount),
//           date: dateTime,
//         };

//         console.log("Sending transaction data:", transactionData);

//         const response = await fetch("http://127.0.0.1:5000/transactions/add", {
//           method: "POST",
//           headers: {
//             "Content-Type": "application/json",
//             "Authorization": `Bearer ${token}`,
//           },
//           body: JSON.stringify(transactionData),
//         });

//         if (!response.ok) {
//           const errorText = await response.text();
//           throw new Error(`Failed to add transaction: ${response.status} ${errorText}`);
//         }

//         const result = await response.json();

//         setMessage({
//           type: 'success',
//           text: `Transaction added successfully! Category: ${result.transaction_category} (${(result.transaction_confidence * 100).toFixed(1)}% confidence)`
//         });

//         // Reset form
//         setFormData({
//           description: '',
//           amount: '',
//           date: new Date().toISOString().split('T')[0],
//           time: new Date().toTimeString().slice(0, 5),
//         });

//         // Refresh all data
//         setTimeout(() => {
//           fetchCombinedData();
//         }, 2000);

//       } catch (err: any) {
//         console.error("Error adding transaction:", err);
//         setMessage({
//           type: 'error',
//           text: err.message || "Failed to add transaction"
//         });
//       } finally {
//         setSubmitting(false);
//       }
//     };

//     const handleChange = (field: keyof TransactionFormData, value: string) => {
//       setFormData(prev => ({
//         ...prev,
//         [field]: value
//       }));
//     };

//     return (
//       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
//         <div
//           className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
//           onClick={(e) => e.stopPropagation()}
//         >
//           <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
//             Add New Transaction
//           </h3>

//           <form onSubmit={handleSubmit} className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium mb-2 font-['Inter']">
//                 Description *
//               </label>
//               <input
//                 type="text"
//                 required
//                 value={formData.description}
//                 onChange={(e) => handleChange('description', e.target.value)}
//                 placeholder="e.g., Grocery shopping, Salary, etc."
//                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//               />
//             </div>

//             <div>
//               <label className="block text-sm font-medium mb-2 font-['Inter']">
//                 Amount *
//               </label>
//               <input
//                 type="number"
//                 step="0.01"
//                 required
//                 value={formData.amount}
//                 onChange={(e) => handleChange('amount', e.target.value)}
//                 placeholder="0.00"
//                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//               />
//               <p className="text-xs text-muted-foreground mt-1">
//                 Use positive for income, negative for expenses (e.g., -50.00)
//               </p>
//             </div>

//             <div className="grid grid-cols-2 gap-4">
//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Date
//                 </label>
//                 <input
//                   type="date"
//                   value={formData.date}
//                   onChange={(e) => handleChange('date', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Time
//                 </label>
//                 <input
//                   type="time"
//                   value={formData.time}
//                   onChange={(e) => handleChange('time', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>
//             </div>

//             {message && (
//               <div className={`p-3 rounded-lg ${message.type === 'success'
//                 ? 'bg-green-500/10 text-green-600 border border-green-500/20'
//                 : 'bg-red-500/10 text-red-600 border border-red-500/20'
//                 }`}>
//                 <p className="text-sm font-['Inter']">{message.text}</p>
//               </div>
//             )}

//             <div className="flex gap-3 pt-2">
//               <Button
//                 type="button"
//                 variant="outline"
//                 className="flex-1"
//                 onClick={() => setActiveModal(null)}
//                 disabled={submitting}
//               >
//                 Cancel
//               </Button>
//               <Button
//                 type="submit"
//                 className="flex-1 bg-primary hover:bg-primary/90"
//                 disabled={submitting}
//               >
//                 {submitting ? "Adding..." : "Add Transaction"}
//               </Button>
//             </div>
//           </form>
//         </div>
//       </div>
//     );
//   };

//   // Task Modal Component
//   const TaskModal = () => {
//     const [formData, setFormData] = useState<TaskFormData>({
//       task: '',
//       date: new Date().toISOString().split('T')[0],
//       time: new Date().toTimeString().slice(0, 5),
//     });
//     const [submitting, setSubmitting] = useState(false);
//     const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

//     const handleSubmit = async (e: React.FormEvent) => {
//       e.preventDefault();
//       setSubmitting(true);
//       setMessage(null);

//       try {
//         const token = localStorage.getItem("token");
//         if (!token) {
//           throw new Error("No authentication token found");
//         }

//         const taskData = {
//           task: formData.task,
//           date: formData.date,
//           time: formData.time,
//         };

//         console.log("Sending task data:", taskData);

//         const response = await fetch("http://127.0.0.1:5000/tasks", {
//           method: "POST",
//           headers: {
//             "Content-Type": "application/json",
//             "Authorization": `Bearer ${token}`,
//           },
//           body: JSON.stringify(taskData),
//         });

//         if (!response.ok) {
//           const errorText = await response.text();
//           throw new Error(`Failed to add task: ${response.status} ${errorText}`);
//         }

//         const result = await response.json();

//         setMessage({
//           type: 'success',
//           text: result.message || "Task added successfully!"
//         });

//         // Reset form
//         setFormData({
//           task: '',
//           date: new Date().toISOString().split('T')[0],
//           time: new Date().toTimeString().slice(0, 5),
//         });

//         // Refresh tasks data
//         setTimeout(() => {
//           fetchCombinedData();
//         }, 2000);

//       } catch (err: any) {
//         console.error("Error adding task:", err);
//         setMessage({
//           type: 'error',
//           text: err.message || "Failed to add task"
//         });
//       } finally {
//         setSubmitting(false);
//       }
//     };

//     const handleChange = (field: keyof TaskFormData, value: string) => {
//       setFormData(prev => ({
//         ...prev,
//         [field]: value
//       }));
//     };

//     return (
//       <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
//         <div
//           className="bg-card rounded-xl p-6 max-w-md w-full border border-border"
//           onClick={(e) => e.stopPropagation()}
//         >
//           <h3 className="font-['Poppins'] font-semibold text-xl mb-4">
//             Add New Task
//           </h3>

//           <form onSubmit={handleSubmit} className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium mb-2 font-['Inter']">
//                 Task Description *
//               </label>
//               <textarea
//                 required
//                 value={formData.task}
//                 onChange={(e) => handleChange('task', e.target.value)}
//                 placeholder="e.g., Pay electricity bill, Review budget, etc."
//                 className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px] resize-none"
//                 rows={3}
//               />
//             </div>

//             <div className="grid grid-cols-2 gap-4">
//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Date
//                 </label>
//                 <input
//                   type="date"
//                   value={formData.date}
//                   onChange={(e) => handleChange('date', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>

//               <div>
//                 <label className="block text-sm font-medium mb-2 font-['Inter']">
//                   Time
//                 </label>
//                 <input
//                   type="time"
//                   value={formData.time}
//                   onChange={(e) => handleChange('time', e.target.value)}
//                   className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
//                 />
//               </div>
//             </div>

//             {message && (
//               <div className={`p-3 rounded-lg ${message.type === 'success'
//                 ? 'bg-green-500/10 text-green-600 border border-green-500/20'
//                 : 'bg-red-500/10 text-red-600 border border-red-500/20'
//                 }`}>
//                 <p className="text-sm font-['Inter']">{message.text}</p>
//               </div>
//             )}

//             <div className="flex gap-3 pt-2">
//               <Button
//                 type="button"
//                 variant="outline"
//                 className="flex-1"
//                 onClick={() => setActiveModal(null)}
//                 disabled={submitting}
//               >
//                 Cancel
//               </Button>
//               <Button
//                 type="submit"
//                 className="flex-1 bg-primary hover:bg-primary/90"
//                 disabled={submitting}
//               >
//                 {submitting ? "Adding..." : "Add Task"}
//               </Button>
//             </div>
//           </form>
//         </div>
//       </div>
//     );
//   };

//   // Fetch combined data (manual transactions + bank data)
//   const fetchCombinedData = async () => {
//     setLoading(true);
//     setError(null);
//     try {
//       const token = localStorage.getItem("token");
//       if (!token) {
//         throw new Error("No token found in localStorage");
//       }

//       // Fetch all data sources in parallel
//       const [taskRes, transactionRes, bankAccountsRes, bankTransactionsRes] = await Promise.all([
//         fetch("http://127.0.0.1:5000/simple-tasks", {
//           headers: { Authorization: `Bearer ${token}` },
//         }).catch(() => {
//           console.log("Tasks endpoint failed, using fallback");
//           return new Response(JSON.stringify({ tasks: [] }));
//         }),
//         fetch("http://127.0.0.1:5000/transactions", {
//           headers: { Authorization: `Bearer ${token}` },
//         }),
//         fetch("http://127.0.0.1:5000/bank/accounts", {
//           headers: { Authorization: `Bearer ${token}` },
//         }).catch(() => new Response(JSON.stringify([]))),
//         fetch("http://127.0.0.1:5000/bank/transactions?days=30", {
//           headers: { Authorization: `Bearer ${token}` },
//         }).catch(() => new Response(JSON.stringify([]))),
//       ]);

//       // Handle tasks
//       let tasksData = { tasks: [] };
//       if (taskRes.ok) {
//         try {
//           tasksData = await taskRes.json();
//         } catch (e) {
//           console.log("Failed to parse tasks response, using fallback");
//         }
//       }
//       setTasks(tasksData.tasks || []);

//       // Handle manual transactions
//       let manualTransactions: Transaction[] = [];
//       if (transactionRes.ok) {
//         const transactionData = await transactionRes.json();
//         const backendTransactions: BackendTransaction[] =
//           Array.isArray(transactionData) ? transactionData : transactionData.transactions || [];

//         manualTransactions = backendTransactions.map((t) => {
//           const rawDate = t.date ?? new Date().toISOString();
//           const friendly = format(parseISO(rawDate), "PPP, p");
//           return {
//             id: t.id,
//             name: t.description || t.category || "Transaction",
//             category: t.category || "Other",
//             amount: t.amount || 0,
//             date: friendly,
//             rawDate,
//           };
//         });

//         manualTransactions.sort((a, b) => (parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime()));
//         setTransactions(manualTransactions);
//       }

//       // Handle bank accounts
//       let bankAccountsData: BankAccount[] = [];
//       if (bankAccountsRes.ok) {
//         bankAccountsData = await bankAccountsRes.json();
//         setBankAccounts(bankAccountsData);
//       }

//       // Handle bank transactions
//       let bankTransactionsData: BankTransaction[] = [];
//       if (bankTransactionsRes.ok) {
//         bankTransactionsData = await bankTransactionsRes.json();
//         setBankTransactions(bankTransactionsData);
//       }

//       // Compute combined financial data
//       computeCombinedFinancialData(manualTransactions, bankAccountsData, bankTransactionsData);

//     } catch (err: any) {
//       console.error("Error fetching data:", err);
//       setError(err.message || "Failed to fetch data");
//     } finally {
//       setLoading(false);
//     }
//   };

//   // Compute combined financial data from all sources
//   const computeCombinedFinancialData = (
//     manualTxns: Transaction[],
//     bankAccounts: BankAccount[],
//     bankTxns: BankTransaction[]
//   ) => {
//     // Calculate totals from bank accounts
//     const bankBalance = bankAccounts.reduce((sum, account) => sum + account.balance_current, 0);

//     // Calculate totals from manual transactions
//     const manualIncome = manualTxns.reduce((sum, t) => sum + (t.amount > 0 ? t.amount : 0), 0);
//     const manualExpenses = manualTxns.reduce((sum, t) => sum + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);
//     const manualNet = manualIncome - manualExpenses;

//     // Calculate totals from bank transactions
//     const bankIncome = bankTxns.reduce((sum, t) => sum + (t.amount > 0 ? t.amount : 0), 0);
//     const bankExpenses = bankTxns.reduce((sum, t) => sum + (t.amount < 0 ? Math.abs(t.amount) : 0), 0);

//     // Combined totals
//     const combinedBalance = bankBalance + manualNet;
//     const combinedIncome = manualIncome + bankIncome;
//     const combinedExpenses = manualExpenses + bankExpenses;

//     setTotalBalance(combinedBalance);
//     setTotalIncome(combinedIncome);
//     setTotalExpenses(combinedExpenses);

//     // Savings progress
//     const targetSavings = Math.max(4500, combinedIncome * 0.5);
//     const currentSavings = Math.max(0, combinedIncome - combinedExpenses);
//     const progress = targetSavings > 0 ? Math.min(100, Math.round((currentSavings / targetSavings) * 100)) : 0;
//     setSavingsProgress(progress);

//     // Combine recent transactions (manual + bank)
//     const allTransactions: Transaction[] = [
//       ...manualTxns,
//       ...bankTxns.map(t => ({
//         id: t.id,
//         name: t.description,
//         category: t.category,
//         amount: t.amount,
//         date: format(parseISO(t.date), "PPP, p"),
//         rawDate: t.date,
//         icon: "🏦" // Bank icon for bank transactions
//       }))
//     ].sort((a, b) => parseISO(b.rawDate).getTime() - parseISO(a.rawDate).getTime())
//       .slice(0, 5);

//     setRecentTransactions(allTransactions);

//     // Category spending (from both manual and bank transactions)
//     const catMap = new Map<string, number>();

//     // Add manual transactions
//     for (const t of manualTxns) {
//       const cat = t.category || "Other";
//       const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
//       catMap.set(cat, (catMap.get(cat) || 0) + amt);
//     }

//     // Add bank transactions
//     for (const t of bankTxns) {
//       const cat = t.category || "Other";
//       const amt = t.amount < 0 ? Math.abs(t.amount) : 0;
//       catMap.set(cat, (catMap.get(cat) || 0) + amt);
//     }

//     const categoryArr = Array.from(catMap.entries()).map(([category, amount]) => ({ category, amount }));
//     categoryArr.sort((a, b) => b.amount - a.amount);
//     setCategorySpending(categoryArr);

//     // Pie data
//     const pie = categoryArr.slice(0, 6).map((c, i) => ({
//       name: c.category,
//       value: c.amount,
//       color: COLORS[i % COLORS.length],
//     }));
//     if (pie.length === 0) {
//       setPieData([{ name: "Other", value: 1, color: COLORS[0] }]);
//     } else {
//       setPieData(pie);
//     }

//     // Weekly balance (using manual transactions for now)
//     const today = new Date();
//     const days = eachDayOfInterval({ start: subDays(startOfDay(today), 6), end: startOfDay(today) });
//     const ascTxns = [...manualTxns].sort((a, b) => parseISO(a.rawDate).getTime() - parseISO(b.rawDate).getTime());
//     const balances: { day: string; balance: number }[] = [];

//     for (const day of days) {
//       const dayStart = startOfDay(day);
//       const dayEnd = endOfDay(day);
//       const cumulative = ascTxns
//         .filter((t) => parseISO(t.rawDate) <= dayEnd)
//         .reduce((acc, t) => acc + (t.amount ?? 0), 0);

//       balances.push({
//         day: format(day, "EEE"),
//         balance: Math.round(cumulative * 100) / 100,
//       });
//     }

//     setWeeklyBalance(balances);
//   };

//   // Fetch data on component mount
//   useEffect(() => {
//     fetchCombinedData();
//     fetchUserProfile();
//   }, []);

//   if (loading) {
//     return (
//       <div className="min-h-screen flex items-center justify-center">
//         <p>Loading dashboard...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="min-h-screen flex items-center justify-center">
//         <p>Error loading dashboard: {error}</p>
//       </div>
//     );
//   }

//   return (
//     <div className="min-h-screen bg-background">
//       {/* Sidebar */}
//       <aside className="fixed left-0 top-0 h-full w-64 bg-card border-r border-border p-6 hidden lg:block">
//         <div className="flex items-center gap-2 mb-8">
//           <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
//             <Wallet className="w-6 h-6 text-white" />
//           </div>
//           <h1 className="font-['Poppins'] font-bold text-xl">Ohmatt</h1>
//         </div>

//         <nav className="space-y-2">
//           <Button
//             variant="default"
//             className="w-full justify-start gap-3 bg-primary text-primary-foreground"
//           >
//             <LayoutDashboard className="w-5 h-5" />
//             Dashboard
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("transactions")}
//           >
//             <CreditCard className="w-5 h-5" />
//             Transactions
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("bank-connection")}
//           >
//             <Banknote className="w-5 h-5" />
//             Bank Connections
//             {bankAccounts.length > 0 && (
//               <Badge className="ml-auto bg-green-500/10 text-green-600 border-green-500/20">
//                 {bankAccounts.length}
//               </Badge>
//             )}
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("messages")}
//           >
//             <MessageSquare className="w-5 h-5" />
//             Messages
//             <Badge className="ml-auto bg-accent">3</Badge>
//           </Button>
//           <Button
//             variant="ghost"
//             className="w-full justify-start gap-3"
//             onClick={() => onNavigate("settings")}
//           >
//             <Settings className="w-5 h-5" />
//             Settings
//           </Button>
//         </nav>

//         <div className="mt-8 p-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-lg border border-primary/20">
//           <ShieldCheck className="w-8 h-8 text-primary mb-2" />
//           <h4 className="font-['Poppins'] font-semibold mb-1">Pro Features</h4>
//           <p className="text-sm text-muted-foreground mb-3 font-['Inter']">
//             Unlock advanced analytics and insights
//           </p>
//           <Button size="sm" className="w-full bg-primary">
//             Upgrade Now
//           </Button>
//         </div>
//       </aside>

//       {/* Main Content */}
//       <div className="lg:ml-64">
//         {/* Header */}
//         <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
//           <div className="px-4 sm:px-6 lg:px-8 py-4">
//             <div className="flex items-center justify-between">
//               <div>
//                 <h2 className="font-['Poppins'] font-bold text-2xl">Dashboard</h2>
//                 <p className="text-muted-foreground font-['Inter']">
//                   Welcome back! Here's your financial overview.
//                   {bankAccounts.length > 0 && (
//                     <span className="text-green-600 ml-2">
//                       • {bankAccounts.length} bank account{bankAccounts.length > 1 ? 's' : ''} connected
//                     </span>
//                   )}
//                 </p>
//               </div>
//               <div className="flex items-center gap-3">
//                 <ThemeToggle />
//                 <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
//                   <span className="text-white font-['Inter'] font-semibold">
//                     {userProfile ? getInitials(userProfile.user) : 'JD'}
//                   </span>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </header>

//         {/* Rest of your dashboard content remains the same */}
//         <main className="p-4 sm:p-6 lg:p-8">
//           {/* Stats Cards */}
//           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
//             <Card className="p-6 hover:shadow-lg transition-all duration-200 border-border bg-card">
//               <div className="flex items-center justify-between mb-4">
//                 <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
//                   <Wallet className="w-6 h-6 text-primary" />
//                 </div>
//                 <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
//                   <TrendingUp className="w-3 h-3 mr-1" />
//                   +12.5%
//                 </Badge>
//               </div>
//               <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
//                 Total Balance
//               </p>
//               <h3 className="font-['Poppins'] font-bold text-2xl">${totalBalance.toFixed(2)}</h3>
//               {bankAccounts.length > 0 && (
//                 <p className="text-xs text-green-600 mt-1">
//                   Includes {bankAccounts.length} bank account{bankAccounts.length > 1 ? 's' : ''}
//                 </p>
//               )}
//             </Card>

//             {/* ... rest of your dashboard content ... */}
//           </div>

//           {/* Charts Section */}
//           <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
//             {/* Monthly Expenses Chart */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Monthly Expenses
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Breakdown by category
//                   </p>
//                 </div>
//                 <Button variant="ghost" size="icon">
//                   <MoreVertical className="w-4 h-4" />
//                 </Button>
//               </div>
//               <ResponsiveContainer width="100%" height={280}>
//                 <PieChart>
//                   <Pie
//                     data={pieData}
//                     cx="50%"
//                     cy="50%"
//                     innerRadius={60}
//                     outerRadius={100}
//                     paddingAngle={5}
//                     dataKey="value"
//                   >
//                     {pieData.map((entry, index) => (
//                       <Cell key={`cell-${index}`} fill={entry.color} />
//                     ))}
//                   </Pie>
//                   <Tooltip />
//                   <Legend />
//                 </PieChart>
//               </ResponsiveContainer>
//             </Card>

//             {/* Weekly Balance Chart */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Weekly Balance
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Balance trend over the week
//                   </p>
//                 </div>
//                 <Button variant="ghost" size="icon">
//                   <MoreVertical className="w-4 h-4" />
//                 </Button>
//               </div>
//               <ResponsiveContainer width="100%" height={280}>
//                 <LineChart data={weeklyBalance}>
//                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
//                   <XAxis dataKey="day" stroke="var(--color-muted-foreground)" />
//                   <YAxis stroke="var(--color-muted-foreground)" />
//                   <Tooltip
//                     contentStyle={{
//                       backgroundColor: "var(--color-card)",
//                       border: "1px solid var(--color-border)",
//                       borderRadius: "8px",
//                     }}
//                   />
//                   <Line
//                     type="monotone"
//                     dataKey="balance"
//                     stroke="#4A90E2"
//                     strokeWidth={3}
//                     dot={{ fill: "#4A90E2", r: 5 }}
//                   />
//                 </LineChart>
//               </ResponsiveContainer>
//             </Card>

//             {/* Category Spending Chart */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Category Spending
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Top spending categories
//                   </p>
//                 </div>
//                 <Button variant="ghost" size="icon">
//                   <MoreVertical className="w-4 h-4" />
//                 </Button>
//               </div>
//               <ResponsiveContainer width="100%" height={280}>
//                 <BarChart data={categorySpending}>
//                   <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
//                   <XAxis dataKey="category" stroke="var(--color-muted-foreground)" />
//                   <YAxis stroke="var(--color-muted-foreground)" />
//                   <Tooltip
//                     contentStyle={{
//                       backgroundColor: "var(--color-card)",
//                       border: "1px solid var(--color-border)",
//                       borderRadius: "8px",
//                     }}
//                   />
//                   <Bar dataKey="amount" fill="#4A90E2" radius={[8, 8, 0, 0]} />
//                 </BarChart>
//               </ResponsiveContainer>
//             </Card>

//             {/* Recent Transactions */}
//             <Card className="p-6 border-border bg-card">
//               <div className="flex items-center justify-between mb-6">
//                 <div>
//                   <h3 className="font-['Poppins'] font-semibold text-lg mb-1">
//                     Recent Transactions
//                   </h3>
//                   <p className="text-sm text-muted-foreground font-['Inter']">
//                     Latest activity
//                   </p>
//                 </div>
//                 <Button
//                   variant="ghost"
//                   size="sm"
//                   onClick={() => onNavigate("transactions")}
//                 >
//                   View All
//                 </Button>
//               </div>
//               <div className="space-y-4">
//                 {recentTransactions.map((transaction) => (
//                   <div
//                     key={transaction.id}
//                     className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
//                   >
//                     <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center text-xl">
//                       {transaction.icon || "💳"}
//                     </div>
//                     <div className="flex-1 min-w-0">
//                       <p className="font-['Inter'] font-medium truncate">
//                         {transaction.name}
//                       </p>
//                       <p className="text-sm text-muted-foreground font-['Inter']">
//                         {transaction.date}
//                       </p>
//                     </div>
//                     <div
//                       className={`font-['Inter'] font-semibold ${transaction.amount > 0 ? "text-secondary" : "text-foreground"
//                         }`}
//                     >
//                       {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </Card>
//           </div>

//           {/* Quick Actions & Tasks */}
//           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//             {/* Quick Actions */}
//             <Card className="p-6 border-border bg-card lg:col-span-2">
//               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Quick Actions</h3>
//               <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-primary hover:bg-primary/90 shadow-md hover:shadow-lg transition-all"
//                   onClick={() => setActiveModal("transaction")}
//                 >
//                   <Plus className="w-6 h-6" />
//                   <span>Add Transaction</span>
//                 </Button>
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-secondary hover:bg-secondary/90 text-secondary-foreground shadow-md hover:shadow-lg transition-all"
//                   onClick={() => setActiveModal("task")}
//                 >
//                   <Plus className="w-6 h-6" />
//                   <span>Add Task</span>
//                 </Button>
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-green-600 hover:bg-green-700 shadow-md hover:shadow-lg transition-all"
//                   onClick={() => onNavigate("bank-connection")}
//                 >
//                   <Banknote className="w-6 h-6" />
//                   <span>Connect Bank</span>
//                 </Button>
//                 <Button
//                   className="h-auto py-6 flex-col gap-2 bg-accent hover:bg-accent/90 shadow-md hover:shadow-lg transition-all"
//                   onClick={() => onNavigate("messages")}
//                 >
//                   <MessageSquare className="w-6 h-6" />
//                   <span>AI Assistant</span>
//                 </Button>
//               </div>
//             </Card>

//             {/* Upcoming Tasks */}
//             <Card className="p-6 border-border bg-card">
//               <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Upcoming Tasks</h3>
//               <div className="space-y-3">
//                 {tasks.map((task) => (
//                   <div
//                     key={task.id}
//                     className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
//                   >
//                     <div className="flex items-start gap-3">
//                       <input
//                         type="checkbox"
//                         className="mt-1 w-4 h-4 rounded border-border"
//                       />
//                       <div className="flex-1">
//                         <p className="font-['Inter'] font-medium">{task.task}</p>
//                         <div className="flex items-center gap-2 mt-1">
//                           <p className="text-xs text-muted-foreground">
//                             {format(parseISO(task.date), "MMM d")} at {task.time}
//                           </p>
//                         </div>
//                       </div>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </Card>
//           </div>
//         </main>
//       </div>

//       {/* Modals */}
//       {activeModal === "transaction" && <TransactionModal />}
//       {activeModal === "task" && <TaskModal />}
//     </div>
//   );
// }