import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { authUtils, User } from '../utils/auth';
import { 
  Brain, 
  Settings, 
  LogOut, 
  BarChart3, 
  Users, 
  Shield, 
  FileText,
  Activity,
  Database,
  Server,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  UserPlus,
  Settings as SettingsIcon,
  Database as DatabaseIcon,
  Shield as ShieldIcon
} from 'lucide-react';

const AdminDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const currentUser = authUtils.getUser();
    if (!currentUser || currentUser.role !== 'admin') {
      navigate('/login');
      return;
    }
    setUser(currentUser);
  }, [navigate]);

  const handleLogout = async () => {
    try {
      authUtils.removeUser();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const adminFeatures = [
    {
      icon: <Users className="w-6 h-6" />,
      title: "User Management",
      description: "Manage users, roles, and permissions",
      link: "/admin/users",
      color: "from-blue-500 to-blue-600"
    },
    {
      icon: <Database className="w-6 h-6" />,
      title: "System Analytics",
      description: "Monitor system performance and usage",
      link: "/admin/analytics",
      color: "from-green-500 to-green-600"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Security Settings",
      description: "Configure security policies and access controls",
      link: "/admin/security",
      color: "from-red-500 to-red-600"
    },
    {
      icon: <Server className="w-6 h-6" />,
      title: "System Configuration",
      description: "Manage system settings and integrations",
      link: "/admin/config",
      color: "from-purple-500 to-purple-600"
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: "Document Management",
      description: "Administer document processing and storage",
      link: "/admin/documents",
      color: "from-orange-500 to-orange-600"
    },
    {
      icon: <Activity className="w-6 h-6" />,
      title: "System Monitoring",
      description: "Real-time system health and alerts",
      link: "/admin/monitoring",
      color: "from-indigo-500 to-indigo-600"
    }
  ];

  const systemStats = [
    {
      title: "Active Users",
      value: "1,247",
      change: "+12%",
      changeType: "positive",
      icon: <Users className="w-5 h-5" />
    },
    {
      title: "Documents Processed",
      value: "15,892",
      change: "+8%",
      changeType: "positive",
      icon: <FileText className="w-5 h-5" />
    },
    {
      title: "System Uptime",
      value: "99.9%",
      change: "+0.1%",
      changeType: "positive",
      icon: <CheckCircle className="w-5 h-5" />
    },
    {
      title: "Response Time",
      value: "1.2s",
      change: "-15%",
      changeType: "positive",
      icon: <Clock className="w-5 h-5" />
    }
  ];

  const recentActivities = [
    {
      type: "user",
      action: "New user registered",
      details: "john.doe@company.com",
      time: "2 minutes ago",
      status: "success"
    },
    {
      type: "document",
      action: "Document processed",
      details: "Network_Layout.pdf",
      time: "5 minutes ago",
      status: "success"
    },
    {
      type: "system",
      action: "System backup completed",
      details: "Daily backup",
      time: "1 hour ago",
      status: "success"
    },
    {
      type: "alert",
      action: "High memory usage",
      details: "85% of available memory",
      time: "2 hours ago",
      status: "warning"
    }
  ];

  const quickActions = [
    {
      icon: <UserPlus className="w-4 h-4" />,
      title: "Add User",
      description: "Create new user account"
    },
    {
      icon: <SettingsIcon className="w-4 h-4" />,
      title: "System Settings",
      description: "Configure system parameters"
    },
    {
      icon: <DatabaseIcon className="w-4 h-4" />,
      title: "Backup Database",
      description: "Create system backup"
    },
    {
      icon: <ShieldIcon className="w-4 h-4" />,
      title: "Security Audit",
      description: "Run security assessment"
    }
  ];

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-red-600 to-red-700 rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">AI Force Admin</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <Avatar className="w-8 h-8">
                  <AvatarImage src="" />
                  <AvatarFallback className="bg-gradient-to-r from-red-500 to-red-600 text-white text-sm">
                    {user.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block">
                  <p className="text-sm font-medium text-gray-900">{user.name}</p>
                  <p className="text-xs text-red-600 font-medium">Administrator</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Admin Dashboard
          </h1>
          <p className="text-gray-600">
            Welcome back, {user.name}. Here's your system overview.
          </p>
        </div>

        {/* System Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {systemStats.map((stat, index) => (
            <Card key={index} className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                  <div className="flex flex-col items-end">
                    <div className="text-blue-600 mb-1">
                      {stat.icon}
                    </div>
                    <div className={`text-sm font-medium ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => (
              <Card key={index} className="border-0 shadow-sm hover:shadow-md transition-shadow duration-200 cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                      {action.icon}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{action.title}</p>
                      <p className="text-sm text-gray-600">{action.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Admin Features Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Administrative Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {adminFeatures.map((feature, index) => (
              <Link key={index} to={feature.link}>
                <Card className="border-0 shadow-sm hover:shadow-md transition-shadow duration-200 cursor-pointer">
                  <CardHeader className="pb-3">
                    <div className={`w-12 h-12 bg-gradient-to-r ${feature.color} rounded-lg flex items-center justify-center text-white mb-3`}>
                      {feature.icon}
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-gray-600">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Activity and System Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-blue-600" />
                <span>Recent Activity</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivities.map((activity, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.status === 'success' ? 'bg-green-500' : 'bg-yellow-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                      <p className="text-xs text-gray-500">{activity.details} • {activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <span>System Health</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">CPU Usage</span>
                    <span className="text-sm text-gray-600">45%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '45%' }}></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Memory Usage</span>
                    <span className="text-sm text-gray-600">67%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '67%' }}></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Storage Usage</span>
                    <span className="text-sm text-gray-600">23%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-500 h-2 rounded-full" style={{ width: '23%' }}></div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Network Load</span>
                    <span className="text-sm text-gray-600">12%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-orange-500 h-2 rounded-full" style={{ width: '12%' }}></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage; 