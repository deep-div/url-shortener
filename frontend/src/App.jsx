import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar.jsx';
import HomePage from './pages/HomePage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <p className="footer-text">
          Built with <strong>snip</strong> — links that tell stories.
        </p>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/analytics/:code" element={<AnalyticsPage />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}
