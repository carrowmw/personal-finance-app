import { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  CssBaseline,
} from "@mui/material";
import PersonIcon from "@mui/icons-material/Person";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ReceiptIcon from "@mui/icons-material/Receipt";
import SettingsIcon from "@mui/icons-material/Settings";

const drawerWidth = 240;

interface DashboardLayoutProps {
  children: React.ReactNode;
  onLogout: () => void;
  onManualSync: () => void;
  onLinkAnotherAccount: () => void;
}

export function DashboardLayout({
  children,
  onLogout,
  onManualSync,
  onLinkAnotherAccount,
}: DashboardLayoutProps) {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) =>
    setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleAction = (action: () => void) => {
    handleMenuClose();
    action();
  };

  return (
    <Box sx={{ display: "flex", bgcolor: "#f9fafb", minHeight: "100vh" }}>
      <CssBaseline />

      {/* Top App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: "white",
          color: "text.primary",
          elevation: 1,
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{ flexGrow: 1, fontWeight: "bold" }}
          >
            Personal Finances
          </Typography>
          <IconButton onClick={handleMenuOpen} color="inherit">
            <Avatar sx={{ bgcolor: "primary.main", width: 32, height: 32 }}>
              <PersonIcon />
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => handleAction(onManualSync)}>
              Force Sync Data
            </MenuItem>
            <MenuItem onClick={() => handleAction(onLinkAnotherAccount)}>
              Link Another Account
            </MenuItem>
            <MenuItem
              onClick={() => handleAction(onLogout)}
              sx={{ color: "error.main" }}
            >
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: drawerWidth,
            boxSizing: "border-box",
            bgcolor: "white",
          },
        }}
      >
        <Toolbar /> {/* Spacer to push content below AppBar */}
        <Box sx={{ overflow: "auto" }}>
          <List>
            <ListItem disablePadding>
              <ListItemButton selected>
                <ListItemIcon>
                  <DashboardIcon color="primary" />
                </ListItemIcon>
                <ListItemText primary="Dashboard" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <ReceiptIcon />
                </ListItemIcon>
                <ListItemText primary="Tax Reports" />
              </ListItemButton>
            </ListItem>
          </List>
          <Divider />
          <List>
            <ListItem disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText primary="Settings" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Main Content Area */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar /> {/* Spacer */}
        {children}
      </Box>
    </Box>
  );
}
