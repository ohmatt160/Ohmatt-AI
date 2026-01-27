// import { useState, useEffect } from "react";
// import { usePlaidLink } from "react-plaid-link";
// import { Button } from "./ui/button";
// import { Card } from "./ui/card";
// import { 
//   ArrowLeft, 
//   Plus, 
//   RefreshCw, 
//   Banknote, 
//   CreditCard,
//   Wallet,
//   TrendingUp,
//   TrendingDown
// } from "lucide-react";
// import { Badge } from "./ui/badge";

// interface BankConnectionProps {
//   onNavigate: (page: string) => void;
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


// export function BankConnection({ onNavigate }: BankConnectionProps) {
//   const [accounts, setAccounts] = useState<BankAccount[]>([]);
//   const [transactions, setTransactions] = useState<BankTransaction[]>([]);
//   const [loading, setLoading] = useState(false);
//   const [syncing, setSyncing] = useState(false);
//   const [financialSummary, setFinancialSummary] = useState({
//     totalBalance: 0,
//     totalIncome: 0,
//     totalExpenses: 0
//   });

  

//     const [linkToken, setLinkToken] = useState<string | null>(null);

//   // Plaid Link configuration
//   const { open, ready } = usePlaidLink({
//     token: linkToken ?? "",
//     onSuccess: async (publicToken: string) => {
//       try {
//         const token = localStorage.getItem("token");
//         await fetch("http://127.0.0.1:5000/bank/exchange_public_token", {
//           method: "POST",
//           headers: {
//             "Content-Type": "application/json",
//             Authorization: `Bearer ${token}`,
//           },
//           body: JSON.stringify({ public_token: publicToken }),
//         });
//         console.log("Bank linked successfully");
//         await fetchBankData();
//         // if (response.ok) {
//         //   console.log("Bank linked successfully");
//         //   await fetchBankData();
//         // } else {
//         //   console.error("Failed to exchange public token");
//         // }
//       } catch (error) {
//         console.error("Error exchanging public token:", error);
//       }
//     },
//     onExit: (err, metadata) => {
//       if (err) {
//         console.error("Plaid Link error:", err);
//       }
//       setLinkToken(null); // Reset link token when exit
//     },
//   });


//   // Fetch bank data
//   const fetchBankData = async () => {
//     setLoading(true);
//     try {
//       const token = localStorage.getItem("token");
//       const [accountsRes, transactionsRes] = await Promise.all([
//         fetch("http://127.0.0.1:5000/bank/accounts", {
//           headers: { Authorization: `Bearer ${token}` },
//         }).catch(() => new Response(JSON.stringify([]))),
//         fetch("http://127.0.0.1:5000/bank/transactions?days=30", {
//           headers: { Authorization: `Bearer ${token}` },
//         }).catch(() => new Response(JSON.stringify([]))),
//       ]);

//       if (accountsRes.ok) {
//         const accountsData = await accountsRes.json();
//         setAccounts(Array.isArray(accountsData) ? accountsData : []);
        
//         const totalBalance = accountsData.reduce((sum: number, acc: BankAccount) => 
//           sum + acc.balance_current, 0
//         );
        
//         if (transactionsRes.ok) {
//           const transactionsData = await transactionsRes.json();
//           const transactionsArray = Array.isArray(transactionsData) ? transactionsData : [];
//           setTransactions(transactionsArray);
          
//           const totalIncome = transactionsArray
//             .filter((t: BankTransaction) => t.amount > 0)
//             .reduce((sum: number, t: BankTransaction) => sum + t.amount, 0);
            
//           const totalExpenses = transactionsArray
//             .filter((t: BankTransaction) => t.amount < 0)
//             .reduce((sum: number, t: BankTransaction) => sum + Math.abs(t.amount), 0);
            
//           setFinancialSummary({
//             totalBalance,
//             totalIncome,
//             totalExpenses
//           });
//         }
//       }
//     } catch (error) {
//       console.error("Error fetching bank data:", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   // Sync bank data
//   const syncBankData = async () => {
//     setSyncing(true);
//     try {
//       const token = localStorage.getItem("token");
//       const response = await fetch("http://127.0.0.1:5000/bank/sync", {
//         method: "POST",
//         headers: { 
//           "Content-Type": "application/json",
//           Authorization: `Bearer ${token}` 
//         },
//       }).catch(() => new Response(JSON.stringify({message: "Sync endpoint not available"})));

//       if (response.ok) {
//         await fetchBankData();
//       }
//     } catch (error) {
//       console.error("Error syncing bank data:", error);
//     } finally {
//       setSyncing(false);
//     }
//   };

//   // Connect bank account (placeholder for future implementation)
//   const connectBankAccount = async() => {
//      try {
//     const token = localStorage.getItem("token");

//     // Step 1: Get link token from backend
//     const res = await fetch("http://127.0.0.1:5000/bank/create_link_token", {
//       method: "POST",
//       headers: { Authorization: `Bearer ${token}` },
//     });
//     const data = await res.json();
//      setLinkToken(data.link_token);
//   }
//   //   const linkToken = data.link_token;

//   //   if (!linkToken) throw new Error("Could not get link token");

//   //   setLinkToken(linkToken);
   
//   // } 
//   catch (err) {
//     console.error("Error connecting bank:", err);
//   }
//   };

//   // useEffect(() => {
//   //   let opened = false;
//   //     if (linkToken && ready) {
//   //   open();
//   //   opened = true;
//   // }
//   // }, [linkToken, ready, open]);

//   const accountTypeIcon = (type: string) => {
//     switch (type) {
//       case 'depository': return <Banknote className="w-5 h-5" />;
//       case 'credit': return <CreditCard className="w-5 h-5" />;
//       default: return <Wallet className="w-5 h-5" />;
//     }
//   };

//   const accountTypeLabel = (type: string) => {
//     switch (type) {
//       case 'depository': return 'Bank Account';
//       case 'credit': return 'Credit Card';
//       default: return type;
//     }
//   };

//   return (
//     <div className="min-h-screen bg-background">
//       {/* Header */}
//       <header className="bg-card border-b border-border sticky top-0 z-40 backdrop-blur-sm bg-card/80">
//         <div className="px-4 sm:px-6 lg:px-8 py-4">
//           <div className="flex items-center justify-between">
//             <div className="flex items-center gap-4">
//               <Button
//                 variant="ghost"
//                 size="icon"
//                 onClick={() => onNavigate("dashboard")}
//               >
//                 <ArrowLeft className="w-5 h-5" />
//               </Button>
//               <div>
//                 <h2 className="font-['Poppins'] font-bold text-2xl">Bank Connections</h2>
//                 <p className="text-muted-foreground font-['Inter']">
//                   Connect and manage your bank accounts
//                 </p>
//               </div>
//             </div>
//             <div className="flex items-center gap-3">
//               <Button
//                 onClick={syncBankData}
//                 disabled={syncing || accounts.length === 0}
//                 variant="outline"
//                 size="sm"
//               >
//                 <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
//                 {syncing ? "Syncing..." : "Sync"}
//               </Button>
//               <Button
//                 // onClick={connectBankAccount}
//                 onClick={async () => {
//                    if (!linkToken) {
//                        await connectBankAccount(); // get link token
//               } else if (ready) {
//                 open()   ; // open Plaid
//                   }
//                    }}
//                 className="bg-primary"
//               >
//                 <Plus className="w-4 h-4 mr-2" />
//                 Connect Bank
//               </Button>
//             </div>
//           </div>
//         </div>
//       </header>

//       {/* Main Content */}
//       <main className="p-4 sm:p-6 lg:p-8">
//         {/* Financial Summary */}
//         <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
//           <Card className="p-6 border-border bg-card">
//             <div className="flex items-center gap-4">
//               <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
//                 <Wallet className="w-6 h-6 text-primary" />
//               </div>
//               <div>
//                 <p className="text-sm text-muted-foreground font-['Inter']">Total Balance</p>
//                 <h3 className="font-['Poppins'] font-bold text-2xl">
//                   ${financialSummary.totalBalance.toFixed(2)}
//                 </h3>
//               </div>
//             </div>
//           </Card>

//           <Card className="p-6 border-border bg-card">
//             <div className="flex items-center gap-4">
//               <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
//                 <TrendingUp className="w-6 h-6 text-green-600" />
//               </div>
//               <div>
//                 <p className="text-sm text-muted-foreground font-['Inter']">Total Income</p>
//                 <h3 className="font-['Poppins'] font-bold text-2xl text-green-600">
//                   ${financialSummary.totalIncome.toFixed(2)}
//                 </h3>
//               </div>
//             </div>
//           </Card>

//           <Card className="p-6 border-border bg-card">
//             <div className="flex items-center gap-4">
//               <div className="w-12 h-12 rounded-lg bg-red-500/10 flex items-center justify-center">
//                 <TrendingDown className="w-6 h-6 text-red-600" />
//               </div>
//               <div>
//                 <p className="text-sm text-muted-foreground font-['Inter']">Total Expenses</p>
//                 <h3 className="font-['Poppins'] font-bold text-2xl text-red-600">
//                   ${financialSummary.totalExpenses.toFixed(2)}
//                 </h3>
//               </div>
//             </div>
//           </Card>
//         </div>

//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
//           {/* Connected Accounts */}
//           <div className="space-y-6">
//             <div className="flex items-center justify-between">
//               <h3 className="font-['Poppins'] font-semibold text-lg">Connected Accounts</h3>
//               <Badge variant="outline">
//                 {accounts.length} account{accounts.length !== 1 ? 's' : ''}
//               </Badge>
//             </div>

//             {accounts.length === 0 ? (
//               <Card className="p-8 text-center border-border bg-card">
//                 <Banknote className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
//                 <h4 className="font-['Poppins'] font-semibold mb-2">No accounts connected</h4>
//                 <p className="text-muted-foreground mb-4">
//                   Connect your bank accounts to see your balances and transactions in one place.
//                 </p>
//                 <Button onClick={connectBankAccount} className="bg-primary">
//                   <Plus className="w-4 h-4 mr-2" />
//                   Connect Bank Account
//                 </Button>
//               </Card>
//             ) : (
//               <div className="space-y-4">
//                 {accounts.map((account) => (
//                   <Card key={account.id} className="p-4 border-border bg-card">
//                     <div className="flex items-center justify-between">
//                       <div className="flex items-center gap-3">
//                         <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
//                           {accountTypeIcon(account.account_type)}
//                         </div>
//                         <div>
//                           <p className="font-['Inter'] font-medium">
//                             {account.institution_name}
//                           </p>
//                           <p className="text-sm text-muted-foreground">
//                             {account.account_name} • {accountTypeLabel(account.account_type)}
//                           </p>
//                         </div>
//                       </div>
//                       <div className="text-right">
//                         <p className="font-['Inter'] font-semibold">
//                           ${account.balance_current.toFixed(2)}
//                         </p>
//                         <Badge variant="outline" className="bg-green-500/10 text-green-600">
//                           {account.currency}
//                         </Badge>
//                       </div>
//                     </div>
//                   </Card>
//                 ))}
//               </div>
//             )}
//           </div>

//           {/* Recent Transactions */}
//           <div className="space-y-6">
//             <div className="flex items-center justify-between">
//               <h3 className="font-['Poppins'] font-semibold text-lg">Recent Transactions</h3>
//               <Badge variant="outline">
//                 {transactions.length} transactions
//               </Badge>
//             </div>

//             {transactions.length === 0 ? (
//               <Card className="p-8 text-center border-border bg-card">
//                 <CreditCard className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
//                 <h4 className="font-['Poppins'] font-semibold mb-2">No transactions</h4>
//                 <p className="text-muted-foreground">
//                   {accounts.length === 0 
//                     ? "Connect a bank account to see your transactions" 
//                     : "No transactions found for the selected period"
//                   }
//                 </p>
//               </Card>
//             ) : (
//               <Card className="border-border bg-card">
//                 <div className="max-h-96 overflow-y-auto">
//                   <div className="space-y-4 p-4">
//                     {transactions.slice(0, 10).map((transaction) => (
//                       <div
//                         key={transaction.id}
//                         className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors"
//                       >
//                         <div className="flex-1 min-w-0">
//                           <p className="font-['Inter'] font-medium truncate">
//                             {transaction.description}
//                           </p>
//                           <div className="flex items-center gap-2 mt-1">
//                             <p className="text-xs text-muted-foreground">
//                               {transaction.merchant_name || transaction.category}
//                             </p>
//                             {transaction.pending && (
//                               <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600">
//                                 Pending
//                               </Badge>
//                             )}
//                           </div>
//                         </div>
//                         <div
//                           className={`font-['Inter'] font-semibold ${
//                             transaction.amount > 0 ? "text-green-600" : "text-foreground"
//                           }`}
//                         >
//                           {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
//                         </div>
//                       </div>
//                     ))}
//                   </div>
//                 </div>
//               </Card>
//             )}
//           </div>
//         </div>

//         {/* Coming Soon Features */}
//         <Card className="mt-8 p-6 border-border bg-card">
//           <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Coming Soon Features</h3>
//           <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
//             <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
//               <Banknote className="w-8 h-8 text-primary mb-2" />
//               <h4 className="font-['Inter'] font-semibold mb-1">Plaid Integration</h4>
//               <p className="text-sm text-muted-foreground">
//                 Secure bank connections with industry-leading security
//               </p>
//             </div>
//             <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
//               <CreditCard className="w-8 h-8 text-secondary mb-2" />
//               <h4 className="font-['Inter'] font-semibold mb-1">Multiple Banks</h4>
//               <p className="text-sm text-muted-foreground">
//                 Connect accounts from different financial institutions
//               </p>
//             </div>
//             <div className="p-4 rounded-lg bg-green-500/5 border border-green-500/20">
//               <RefreshCw className="w-8 h-8 text-green-600 mb-2" />
//               <h4 className="font-['Inter'] font-semibold mb-1">Auto Sync</h4>
//               <p className="text-sm text-muted-foreground">
//                 Automatic transaction updates and balance synchronization
//               </p>
//             </div>
//           </div>
//         </Card>
//       </main>
//     </div>
//   );
// }

import { useState, useEffect } from "react";
import { usePlaidLink } from "react-plaid-link";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { 
  ArrowLeft, 
  Plus, 
  RefreshCw, 
  Banknote, 
  CreditCard,
  Wallet,
  TrendingUp,
  TrendingDown
} from "lucide-react";
import { Badge } from "./ui/badge";

interface BankConnectionProps {
  onNavigate: (page: string) => void;
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

interface FinancialSummary {
  totalBalance: number;
  totalIncome: number;
  totalExpenses: number;
}

export function BankConnection({ onNavigate }: BankConnectionProps) {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [financialSummary, setFinancialSummary] = useState<FinancialSummary>({
    totalBalance: 0,
    totalIncome: 0,
    totalExpenses: 0
  });
  const [linkToken, setLinkToken] = useState<string | null>(null);

  // Plaid Link configuration
  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: async (publicToken: string) => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://127.0.0.1:5000/bank/exchange_public_token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ public_token: publicToken }),
        });
        
        if (response.ok) {
          console.log("Bank linked successfully");
          await fetchBankData();
        } else {
          console.error("Failed to exchange public token");
        }
      } catch (error) {
        console.error("Error exchanging public token:", error);
      }
    },
    onExit: (err, metadata) => {
      if (err) {
        console.error("Plaid Link error:", err);
      }
      setLinkToken(null); // Reset link token when exit
    },
  });

  // Fetch bank data
  const fetchBankData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const [accountsRes, transactionsRes] = await Promise.all([
        fetch("http://127.0.0.1:5000/bank/accounts", {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => new Response(JSON.stringify([]))),
        fetch("http://127.0.0.1:5000/bank/transactions?days=30", {
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => new Response(JSON.stringify([]))),
      ]);

      if (accountsRes.ok) {
        const accountsData = await accountsRes.json();
        setAccounts(Array.isArray(accountsData) ? accountsData : []);
        
        const totalBalance = accountsData.reduce((sum: number, acc: BankAccount) => 
          sum + acc.balance_current, 0
        );
        
        if (transactionsRes.ok) {
          const transactionsData = await transactionsRes.json();
          const transactionsArray = Array.isArray(transactionsData) ? transactionsData : [];
          setTransactions(transactionsArray);
          
          const totalIncome = transactionsArray
            .filter((t: BankTransaction) => t.amount > 0)
            .reduce((sum: number, t: BankTransaction) => sum + t.amount, 0);
            
          const totalExpenses = transactionsArray
            .filter((t: BankTransaction) => t.amount < 0)
            .reduce((sum: number, t: BankTransaction) => sum + Math.abs(t.amount), 0);
            
          setFinancialSummary({
            totalBalance,
            totalIncome,
            totalExpenses
          });
        }
      }
    } catch (error) {
      console.error("Error fetching bank data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Sync bank data
  const syncBankData = async () => {
    setSyncing(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://127.0.0.1:5000/bank/sync", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
      }).catch(() => new Response(JSON.stringify({message: "Sync endpoint not available"})));

      if (response.ok) {
        await fetchBankData();
      }
    } catch (error) {
      console.error("Error syncing bank data:", error);
    } finally {
      setSyncing(false);
    }
  };

  // Connect bank account
  const connectBankAccount = async () => {
    console.log("CONNECT BANK CLICKED");
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://127.0.0.1:5000/bank/link-token", {
        method: "GET",
         credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (!response.ok) {
        throw new Error("Failed to create link token");
      }
      
      const data = await response.json();
      const newLinkToken = data.link_token;
      
      if (!newLinkToken) {
        throw new Error("Could not get link token");
      }
      
      setLinkToken(newLinkToken);
    } catch (error) {
      console.error("Error creating link token:", error);
    }
  };

//   const connectBankAccount = async () => {
//   console.log("CONNECT BANK CLICKED");
//   const token = localStorage.getItem("token");

//   if (!token) {
//     console.error("No token found. User might not be logged in.");
//     return;
//   }

//   try {
//     const response = await fetch("http://127.0.0.1:5000/bank/link-token", {
//       method: "GET",
//       headers: {
//         Authorization: `Bearer ${token}`,
//         "Content-Type": "application/json",
//       },
//     });

//     if (response.status === 401) {
//       console.error("Unauthorized! Token might be invalid or expired.");
//       return;
//     }

//     if (!response.ok) {
//       throw new Error(`Failed to create link token: ${response.statusText}`);
//     }

//     const data = await response.json();
//     const newLinkToken = data.link_token;

//     if (!newLinkToken) {
//       throw new Error("Could not get link token from server");
//     }

//     setLinkToken(newLinkToken); // this will trigger Plaid Link open
//   } catch (error) {
//     console.error("Error creating link token:", error);
//   }
// };


  // Open Plaid Link when linkToken is set
  // useEffect(() => {
  //   if (linkToken && ready) {
  //     open();
  //   }
  // }, [linkToken, ready, open]);
  useEffect(() => {
  if (ready && linkToken) {
    open();
  }
}, [ready, linkToken, open]);


  useEffect(() => {
    fetchBankData();
  }, []);

  const accountTypeIcon = (type: string) => {
    switch (type) {
      case 'depository': return <Banknote className="w-5 h-5" />;
      case 'credit': return <CreditCard className="w-5 h-5" />;
      default: return <Wallet className="w-5 h-5" />;
    }
  };

  const accountTypeLabel = (type: string) => {
    switch (type) {
      case 'depository': return 'Bank Account';
      case 'credit': return 'Credit Card';
      default: return type;
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
                <h2 className="font-['Poppins'] font-bold text-2xl">Bank Connections</h2>
                <p className="text-muted-foreground font-['Inter']">
                  Connect and manage your bank accounts
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={syncBankData}
                disabled={syncing || accounts.length === 0}
                variant="outline"
                size="sm"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? "Syncing..." : "Sync"}
              </Button>
              <Button
                onClick={connectBankAccount}
                className="bg-primary"
              
              >
                <Plus className="w-4 h-4 mr-2" />
                Connect Bank
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-4 sm:p-6 lg:p-8">
        {/* Financial Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6 border-border bg-card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Wallet className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground font-['Inter']">Total Balance</p>
                <h3 className="font-['Poppins'] font-bold text-2xl">
                  ${financialSummary.totalBalance.toFixed(2)}
                </h3>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-border bg-card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground font-['Inter']">Total Income</p>
                <h3 className="font-['Poppins'] font-bold text-2xl text-green-600">
                  ${financialSummary.totalIncome.toFixed(2)}
                </h3>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-border bg-card">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-red-500/10 flex items-center justify-center">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground font-['Inter']">Total Expenses</p>
                <h3 className="font-['Poppins'] font-bold text-2xl text-red-600">
                  ${financialSummary.totalExpenses.toFixed(2)}
                </h3>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Connected Accounts */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="font-['Poppins'] font-semibold text-lg">Connected Accounts</h3>
              <Badge variant="outline">
                {accounts.length} account{accounts.length !== 1 ? 's' : ''}
              </Badge>
            </div>

            {accounts.length === 0 ? (
              <Card className="p-8 text-center border-border bg-card">
                <Banknote className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h4 className="font-['Poppins'] font-semibold mb-2">No accounts connected</h4>
                <p className="text-muted-foreground mb-4">
                  Connect your bank accounts to see your balances and transactions in one place.
                </p>
                <Button 
                  onClick={connectBankAccount} 
                  className="bg-primary"
                  
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Connect Bank Account
                </Button>
              </Card>
            ) : (
              <div className="space-y-4">
                {accounts.map((account) => (
                  <Card key={account.id} className="p-4 border-border bg-card">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          {accountTypeIcon(account.account_type)}
                        </div>
                        <div>
                          <p className="font-['Inter'] font-medium">
                            {account.institution_name}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {account.account_name} • {accountTypeLabel(account.account_type)}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-['Inter'] font-semibold">
                          ${account.balance_current.toFixed(2)}
                        </p>
                        <Badge variant="outline" className="bg-green-500/10 text-green-600">
                          {account.currency}
                        </Badge>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Recent Transactions */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="font-['Poppins'] font-semibold text-lg">Recent Transactions</h3>
              <Badge variant="outline">
                {transactions.length} transactions
              </Badge>
            </div>

            {transactions.length === 0 ? (
              <Card className="p-8 text-center border-border bg-card">
                <CreditCard className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h4 className="font-['Poppins'] font-semibold mb-2">No transactions</h4>
                <p className="text-muted-foreground">
                  {accounts.length === 0 
                    ? "Connect a bank account to see your transactions" 
                    : "No transactions found for the selected period"
                  }
                </p>
              </Card>
            ) : (
              <Card className="border-border bg-card">
                <div className="max-h-96 overflow-y-auto">
                  <div className="space-y-4 p-4">
                    {transactions.slice(0, 10).map((transaction) => (
                      <div
                        key={transaction.id}
                        className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="font-['Inter'] font-medium truncate">
                            {transaction.description}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-xs text-muted-foreground">
                              {transaction.merchant_name || transaction.category}
                            </p>
                            {transaction.pending && (
                              <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600">
                                Pending
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div
                          className={`font-['Inter'] font-semibold ${
                            transaction.amount > 0 ? "text-green-600" : "text-foreground"
                          }`}
                        >
                          {transaction.amount > 0 ? "+" : ""}${Math.abs(transaction.amount).toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>

        {/* Coming Soon Features */}
        <Card className="mt-8 p-6 border-border bg-card">
          <h3 className="font-['Poppins'] font-semibold text-lg mb-4">Coming Soon Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
              <Banknote className="w-8 h-8 text-primary mb-2" />
              <h4 className="font-['Inter'] font-semibold mb-1">Plaid Integration</h4>
              <p className="text-sm text-muted-foreground">
                Secure bank connections with industry-leading security
              </p>
            </div>
            <div className="p-4 rounded-lg bg-secondary/5 border border-secondary/20">
              <CreditCard className="w-8 h-8 text-secondary mb-2" />
              <h4 className="font-['Inter'] font-semibold mb-1">Multiple Banks</h4>
              <p className="text-sm text-muted-foreground">
                Connect accounts from different financial institutions
              </p>
            </div>
            <div className="p-4 rounded-lg bg-green-500/5 border border-green-500/20">
              <RefreshCw className="w-8 h-8 text-green-600 mb-2" />
              <h4 className="font-['Inter'] font-semibold mb-1">Auto Sync</h4>
              <p className="text-sm text-muted-foreground">
                Automatic transaction updates and balance synchronization
              </p>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}