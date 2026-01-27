import { useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { ThemeToggle } from "./ThemeToggle";
import {
  ArrowLeft,
  Users,
  Activity,
  MessageSquare,
  TrendingUp,
  Search,
  MoreVertical,
  Shield,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface AdminPanelProps {
  onNavigate: (page: string) => void;
}

export function AdminPanel({ onNavigate }: AdminPanelProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const userGrowthData = [
    { month: "Jan", users: 1200 },
    { month: "Feb", users: 1800 },
    { month: "Mar", users: 2400 },
    { month: "Apr", users: 3100 },
    { month: "May", users: 3800 },
    { month: "Jun", users: 4500 },
  ];

  const transactionVolumeData = [
    { day: "Mon", count: 245 },
    { day: "Tue", count: 312 },
    { day: "Wed", count: 289 },
    { day: "Thu", count: 356 },
    { day: "Fri", count: 428 },
    { day: "Sat", count: 198 },
    { day: "Sun", count: 167 },
  ];

  const recentUsers = [
    {
      id: "U001",
      name: "Alice Thompson",
      email: "alice@example.com",
      status: "active",
      joined: "Oct 30, 2025",
      transactions: 45,
    },
    {
      id: "U002",
      name: "Bob Martinez",
      email: "bob@example.com",
      status: "active",
      joined: "Oct 29, 2025",
      transactions: 32,
    },
    {
      id: "U003",
      name: "Carol White",
      email: "carol@example.com",
      status: "inactive",
      joined: "Oct 28, 2025",
      transactions: 8,
    },
    {
      id: "U004",
      name: "David Lee",
      email: "david@example.com",
      status: "active",
      joined: "Oct 27, 2025",
      transactions: 67,
    },
  ];

  const activityLogs = [
    {
      id: 1,
      user: "Admin",
      action: "Updated system settings",
      timestamp: "2 minutes ago",
      type: "info",
    },
    {
      id: 2,
      user: "Alice Thompson",
      action: "Created new account",
      timestamp: "15 minutes ago",
      type: "success",
    },
    {
      id: 3,
      user: "System",
      action: "Failed login attempt detected",
      timestamp: "1 hour ago",
      type: "warning",
    },
    {
      id: 4,
      user: "Bob Martinez",
      action: "Completed profile verification",
      timestamp: "2 hours ago",
      type: "success",
    },
    {
      id: 5,
      user: "System",
      action: "Database backup completed",
      timestamp: "3 hours ago",
      type: "info",
    },
  ];

  const messages = [
    {
      id: 1,
      from: "Alice Thompson",
      to: "AI Assistant",
      preview: "Can you help me with budget analysis?",
      time: "5m ago",
      status: "unread",
    },
    {
      id: 2,
      from: "Bob Martinez",
      to: "Support Team",
      preview: "Issue with transaction sync",
      time: "1h ago",
      status: "read",
    },
    {
      id: 3,
      from: "Carol White",
      to: "AI Assistant",
      preview: "Thank you for the savings recommendations!",
      time: "2h ago",
      status: "read",
    },
  ];

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
                <h2 className="font-['Poppins'] font-bold text-2xl">Admin Panel</h2>
                <p className="text-muted-foreground font-['Inter']">
                  Manage users, activities, and system settings
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center cursor-pointer">
                <Shield className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="p-4 sm:p-6 lg:px-8 lg:py-6 max-w-7xl mx-auto">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 border-border bg-card hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Users className="w-6 h-6 text-primary" />
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                +12%
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Total Users
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl">4,532</h3>
          </Card>

          <Card className="p-6 border-border bg-card hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
                <Activity className="w-6 h-6 text-secondary" />
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                +8%
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Active Today
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl">1,234</h3>
          </Card>

          <Card className="p-6 border-border bg-card hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-accent" />
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                +15%
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Transactions
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl">28,456</h3>
          </Card>

          <Card className="p-6 border-border bg-card hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
                3 New
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground font-['Inter'] mb-1">
              Messages
            </p>
            <h3 className="font-['Poppins'] font-bold text-2xl">156</h3>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card className="p-6 border-border bg-card">
            <h3 className="font-['Poppins'] font-semibold text-lg mb-6">
              User Growth
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={userGrowthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="month" stroke="var(--color-muted-foreground)" />
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
                  dataKey="users"
                  stroke="#4A90E2"
                  strokeWidth={3}
                  dot={{ fill: "#4A90E2", r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-6 border-border bg-card">
            <h3 className="font-['Poppins'] font-semibold text-lg mb-6">
              Transaction Volume
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={transactionVolumeData}>
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
                <Bar dataKey="count" fill="#50E3C2" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="activity">Activity Logs</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users">
            <Card className="border-border bg-card">
              <div className="p-6 border-b border-border">
                <div className="flex flex-col sm:flex-row gap-4 justify-between">
                  <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-input-background"
                    />
                  </div>
                  <Button className="bg-primary">
                    <Users className="w-4 h-4 mr-2" />
                    Add User
                  </Button>
                </div>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead>Transactions</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentUsers.map((user) => (
                    <TableRow key={user.id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell>
                        <div>
                          <p className="font-['Inter'] font-medium">{user.name}</p>
                          <p className="text-sm text-muted-foreground">{user.email}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            user.status === "active"
                              ? "bg-green-500/10 text-green-600 border-green-500/20"
                              : "bg-gray-500/10 text-gray-600 border-gray-500/20"
                          }
                        >
                          {user.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{user.joined}</TableCell>
                      <TableCell className="font-['Inter'] font-medium">
                        {user.transactions}
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
          </TabsContent>

          {/* Activity Logs Tab */}
          <TabsContent value="activity">
            <Card className="p-6 border-border bg-card">
              <h3 className="font-['Poppins'] font-semibold text-lg mb-6">
                Recent Activity
              </h3>
              <div className="space-y-4">
                {activityLogs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-4 p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        log.type === "success"
                          ? "bg-green-500/10"
                          : log.type === "warning"
                          ? "bg-yellow-500/10"
                          : "bg-primary/10"
                      }`}
                    >
                      {log.type === "success" ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                      ) : log.type === "warning" ? (
                        <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      ) : (
                        <Activity className="w-5 h-5 text-primary" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-['Inter'] font-medium mb-1">{log.action}</p>
                      <p className="text-sm text-muted-foreground">
                        {log.user} • {log.timestamp}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Messages Tab */}
          <TabsContent value="messages">
            <Card className="p-6 border-border bg-card">
              <h3 className="font-['Poppins'] font-semibold text-lg mb-6">
                Message Oversight
              </h3>
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className="flex items-center gap-4 p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer"
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-['Inter'] font-semibold flex-shrink-0">
                      {msg.from[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-['Inter'] font-medium">{msg.from}</p>
                        <span className="text-muted-foreground">→</span>
                        <p className="text-sm text-muted-foreground">{msg.to}</p>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {msg.preview}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground">{msg.time}</span>
                      {msg.status === "unread" && (
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
