import { useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { ThemeToggle } from "./ThemeToggle";
import {
  Search,
  Filter,
  Download,
  ArrowLeft,
  ArrowUpDown,
  MoreVertical,
  Plus,
  Calendar,
} from "lucide-react";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

interface TransactionViewProps {
  onNavigate: (page: string) => void;
}

export function TransactionView({ onNavigate }: TransactionViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [viewMode, setViewMode] = useState<"table" | "card">("card");

  const transactions = [
    {
      id: "TXN001",
      name: "Grocery Store",
      category: "Food",
      amount: -85.5,
      date: "Oct 31, 2025",
      time: "2:30 PM",
      status: "completed",
      icon: "🛒",
    },
    {
      id: "TXN002",
      name: "Salary Deposit",
      category: "Income",
      amount: 3500,
      date: "Oct 31, 2025",
      time: "9:00 AM",
      status: "completed",
      icon: "💰",
    },
    {
      id: "TXN003",
      name: "Uber Ride",
      category: "Transport",
      amount: -15.2,
      date: "Oct 30, 2025",
      time: "6:45 PM",
      status: "completed",
      icon: "🚗",
    },
    {
      id: "TXN004",
      name: "Netflix Subscription",
      category: "Entertainment",
      amount: -12.99,
      date: "Oct 29, 2025",
      time: "12:00 AM",
      status: "completed",
      icon: "🎬",
    },
    {
      id: "TXN005",
      name: "Coffee Shop",
      category: "Food",
      amount: -5.8,
      date: "Oct 29, 2025",
      time: "8:15 AM",
      status: "completed",
      icon: "☕",
    },
    {
      id: "TXN006",
      name: "Amazon Purchase",
      category: "Shopping",
      amount: -42.99,
      date: "Oct 28, 2025",
      time: "3:20 PM",
      status: "pending",
      icon: "📦",
    },
    {
      id: "TXN007",
      name: "Electricity Bill",
      category: "Bills",
      amount: -78.5,
      date: "Oct 27, 2025",
      time: "10:00 AM",
      status: "completed",
      icon: "⚡",
    },
    {
      id: "TXN008",
      name: "Freelance Payment",
      category: "Income",
      amount: 850,
      date: "Oct 26, 2025",
      time: "4:30 PM",
      status: "completed",
      icon: "💼",
    },
  ];

  const filteredTransactions = transactions.filter((txn) => {
    const matchesSearch =
      txn.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      categoryFilter === "all" || txn.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      Food: "bg-primary/10 text-primary border-primary/20",
      Transport: "bg-secondary/10 text-secondary border-secondary/20",
      Entertainment: "bg-accent/10 text-accent border-accent/20",
      Shopping: "bg-purple-500/10 text-purple-600 border-purple-500/20",
      Bills: "bg-red-500/10 text-red-600 border-red-500/20",
      Income: "bg-green-500/10 text-green-600 border-green-500/20",
    };
    return colors[category] || "bg-muted text-muted-foreground";
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
        <div className="px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onNavigate("dashboard")}
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h2 className="font-['Poppins'] font-bold text-2xl">Transactions</h2>
                <p className="text-muted-foreground font-['Inter']">
                  Manage and track all your transactions
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
                <span className="text-white font-['Inter'] font-semibold">JD</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="p-4 sm:p-6 lg:px-8 lg:py-6 max-w-7xl mx-auto">
        {/* Filters and Actions */}
        <Card className="p-6 mb-6 border-border bg-card">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search transactions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-input-background border-border"
              />
            </div>

            {/* Category Filter */}
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-48 bg-input-background">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="Food">Food</SelectItem>
                <SelectItem value="Transport">Transport</SelectItem>
                <SelectItem value="Entertainment">Entertainment</SelectItem>
                <SelectItem value="Shopping">Shopping</SelectItem>
                <SelectItem value="Bills">Bills</SelectItem>
                <SelectItem value="Income">Income</SelectItem>
              </SelectContent>
            </Select>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button variant="outline" className="gap-2">
                <Filter className="w-4 h-4" />
                Filter
              </Button>
              <Button variant="outline" className="gap-2">
                <Download className="w-4 h-4" />
                Export
              </Button>
              <Button className="gap-2 bg-primary">
                <Plus className="w-4 h-4" />
                Add
              </Button>
            </div>
          </div>
        </Card>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
          <Card className="p-6 border-border bg-card">
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Total Transactions
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl">
              {filteredTransactions.length}
            </h3>
          </Card>
          <Card className="p-6 border-border bg-card">
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Total Income
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl text-secondary">
              +$
              {filteredTransactions
                .filter((t) => t.amount > 0)
                .reduce((sum, t) => sum + t.amount, 0)
                .toFixed(2)}
            </h3>
          </Card>
          <Card className="p-6 border-border bg-card">
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Total Expenses
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl">
              -$
              {Math.abs(
                filteredTransactions
                  .filter((t) => t.amount < 0)
                  .reduce((sum, t) => sum + t.amount, 0)
              ).toFixed(2)}
            </h3>
          </Card>
        </div>

        {/* Transactions List */}
        {viewMode === "card" ? (
          <div className="space-y-4">
            {filteredTransactions.map((transaction) => (
              <Card
                key={transaction.id}
                className="p-6 border-border bg-card hover:shadow-lg transition-all duration-200 cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center text-2xl flex-shrink-0">
                    {transaction.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div className="flex-1">
                        <h4 className="font-['Inter'] font-semibold truncate">
                          {transaction.name}
                        </h4>
                        <p className="text-sm text-muted-foreground font-['Inter']">
                          {transaction.date} • {transaction.time}
                        </p>
                      </div>
                      <div
                        className={`font-['Poppins'] font-bold text-xl ${
                          transaction.amount > 0 ? "text-secondary" : "text-foreground"
                        }`}
                      >
                        {transaction.amount > 0 ? "+" : ""}$
                        {Math.abs(transaction.amount).toFixed(2)}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <Badge variant="outline" className={getCategoryColor(transaction.category)}>
                        {transaction.category}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={
                          transaction.status === "completed"
                            ? "bg-green-500/10 text-green-600 border-green-500/20"
                            : "bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
                        }
                      >
                        {transaction.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground font-['Inter']">
                        ID: {transaction.id}
                      </span>
                      <Button variant="ghost" size="icon" className="ml-auto h-8 w-8">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Transaction</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTransactions.map((transaction) => (
                  <TableRow key={transaction.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-lg">
                          {transaction.icon}
                        </div>
                        <div>
                          <p className="font-['Inter'] font-medium">{transaction.name}</p>
                          <p className="text-xs text-muted-foreground">{transaction.id}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getCategoryColor(transaction.category)}>
                        {transaction.category}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {transaction.date}
                      <br />
                      <span className="text-xs text-muted-foreground">{transaction.time}</span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          transaction.status === "completed"
                            ? "bg-green-500/10 text-green-600 border-green-500/20"
                            : "bg-yellow-500/10 text-yellow-600 border-yellow-500/20"
                        }
                      >
                        {transaction.status}
                      </Badge>
                    </TableCell>
                    <TableCell
                      className={`text-right font-['Inter'] font-semibold ${
                        transaction.amount > 0 ? "text-secondary" : "text-foreground"
                      }`}
                    >
                      {transaction.amount > 0 ? "+" : ""}$
                      {Math.abs(transaction.amount).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </main>
    </div>
  );
}
