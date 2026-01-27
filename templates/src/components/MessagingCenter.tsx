import { useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { ThemeToggle } from "./ThemeToggle";
import {
  ArrowLeft,
  Send,
  Paperclip,
  Smile,
  Bot,
  User,
  Circle,
  Search,
  MoreVertical,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { ScrollArea } from "./ui/scroll-area";

interface MessagingCenterProps {
  onNavigate: (page: string) => void;
}

export function MessagingCenter({ onNavigate }: MessagingCenterProps) {
  const [message, setMessage] = useState("");
  const [selectedConversation, setSelectedConversation] = useState("ai-assistant");

  const conversations = [
    {
      id: "ai-assistant",
      name: "AI Assistant",
      lastMessage: "I can help you analyze your spending patterns!",
      time: "2m ago",
      unread: 2,
      isAI: true,
      online: true,
    },
    {
      id: "user-1",
      name: "Sarah Johnson",
      lastMessage: "Thanks for the budget tips!",
      time: "1h ago",
      unread: 0,
      isAI: false,
      online: true,
    },
    {
      id: "user-2",
      name: "Mike Chen",
      lastMessage: "Let's discuss the investment plan",
      time: "3h ago",
      unread: 1,
      isAI: false,
      online: false,
    },
  ];

  const messages = [
    {
      id: 1,
      sender: "ai",
      content: "Hello! I'm your AI financial assistant. How can I help you today?",
      time: "10:00 AM",
    },
    {
      id: 2,
      sender: "user",
      content: "Hi! Can you analyze my spending for this month?",
      time: "10:02 AM",
    },
    {
      id: 3,
      sender: "ai",
      content:
        "Of course! I've analyzed your spending patterns for October. Here's what I found:\n\n• Your largest expense category is Food ($2,400)\n• You're spending 15% more on transport compared to last month\n• Great job staying under budget for entertainment!\n\nWould you like me to provide specific recommendations?",
      time: "10:03 AM",
    },
    {
      id: 4,
      sender: "user",
      content: "Yes, please! What can I do to save more?",
      time: "10:05 AM",
    },
    {
      id: 5,
      sender: "ai",
      content:
        "Based on your spending patterns, here are my top recommendations:\n\n1. **Meal Planning**: You could save ~$300/month by reducing dining out\n2. **Transport**: Consider carpooling to reduce fuel costs by 20%\n3. **Subscriptions**: You have 3 unused subscriptions worth $35/month\n\nImplementing these could save you approximately $400/month!",
      time: "10:06 AM",
    },
  ];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      // Handle message sending
      setMessage("");
    }
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
                <h2 className="font-['Poppins'] font-bold text-2xl">Messages</h2>
                <p className="text-muted-foreground font-['Inter']">
                  Chat with AI assistant and colleagues
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
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-200px)]">
          {/* Conversations List */}
          <Card className="lg:col-span-4 border-border bg-card flex flex-col">
            <div className="p-4 border-b border-border">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search conversations..."
                  className="pl-10 bg-input-background border-border"
                />
              </div>
            </div>
            <ScrollArea className="flex-1">
              <div className="p-2">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => setSelectedConversation(conv.id)}
                    className={`p-4 rounded-lg cursor-pointer transition-all duration-200 mb-2 ${
                      selectedConversation === conv.id
                        ? "bg-primary/10 border border-primary/20"
                        : "hover:bg-muted/50"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="relative">
                        <Avatar className="w-12 h-12">
                          <AvatarFallback
                            className={
                              conv.isAI
                                ? "bg-gradient-to-br from-primary to-secondary text-white"
                                : "bg-muted"
                            }
                          >
                            {conv.isAI ? <Bot className="w-6 h-6" /> : conv.name[0]}
                          </AvatarFallback>
                        </Avatar>
                        {conv.online && (
                          <Circle className="absolute bottom-0 right-0 w-3 h-3 fill-secondary text-secondary" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-['Inter'] font-semibold truncate">
                            {conv.name}
                          </h4>
                          <span className="text-xs text-muted-foreground">
                            {conv.time}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-muted-foreground truncate font-['Inter']">
                            {conv.lastMessage}
                          </p>
                          {conv.unread > 0 && (
                            <Badge className="ml-2 bg-primary text-primary-foreground">
                              {conv.unread}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>

          {/* Chat Area */}
          <Card className="lg:col-span-8 border-border bg-card flex flex-col">
            {/* Chat Header */}
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar className="w-10 h-10">
                  <AvatarFallback className="bg-gradient-to-br from-primary to-secondary text-white">
                    <Bot className="w-5 h-5" />
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="font-['Inter'] font-semibold">AI Assistant</h3>
                  <p className="text-xs text-secondary font-['Inter']">
                    <Circle className="inline w-2 h-2 fill-secondary mr-1" />
                    Online
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${
                      msg.sender === "user" ? "flex-row-reverse" : ""
                    }`}
                  >
                    <Avatar className="w-8 h-8 flex-shrink-0">
                      <AvatarFallback
                        className={
                          msg.sender === "ai"
                            ? "bg-gradient-to-br from-primary to-secondary text-white"
                            : "bg-muted"
                        }
                      >
                        {msg.sender === "ai" ? (
                          <Bot className="w-4 h-4" />
                        ) : (
                          <User className="w-4 h-4" />
                        )}
                      </AvatarFallback>
                    </Avatar>
                    <div
                      className={`flex flex-col ${
                        msg.sender === "user" ? "items-end" : ""
                      }`}
                    >
                      <div
                        className={`max-w-md rounded-2xl px-4 py-3 ${
                          msg.sender === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        }`}
                      >
                        <p className="font-['Inter'] whitespace-pre-line">
                          {msg.content}
                        </p>
                      </div>
                      <span className="text-xs text-muted-foreground mt-1 font-['Inter']">
                        {msg.time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* AI Suggestions */}
            <div className="px-4 py-2 border-t border-border">
              <div className="flex gap-2 overflow-x-auto pb-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="whitespace-nowrap"
                  onClick={() => setMessage("Show my monthly spending")}
                >
                  Show my monthly spending
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="whitespace-nowrap"
                  onClick={() => setMessage("What's my budget status?")}
                >
                  What's my budget status?
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="whitespace-nowrap"
                  onClick={() => setMessage("Suggest savings tips")}
                >
                  Suggest savings tips
                </Button>
              </div>
            </div>

            {/* Message Input */}
            <div className="p-4 border-t border-border">
              <form onSubmit={handleSendMessage} className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <Input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="pr-20 bg-input-background border-border resize-none"
                    multiline
                  />
                  <div className="absolute right-2 bottom-2 flex gap-1">
                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8">
                      <Paperclip className="w-4 h-4" />
                    </Button>
                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8">
                      <Smile className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <Button
                  type="submit"
                  size="icon"
                  className="h-10 w-10 bg-primary hover:bg-primary/90 flex-shrink-0"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
              <p className="text-xs text-muted-foreground mt-2 font-['Inter']">
                AI Assistant can make mistakes. Verify important information.
              </p>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
