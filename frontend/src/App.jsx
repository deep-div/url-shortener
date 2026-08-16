import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NavBar from './components/Navbar.jsx';
import HomePage from './pages/HomePage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';
import RedirectPage from './pages/RedirectPage.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/analytics/:code" element={<AnalyticsPage />} />
        <Route path="/r/:code" element={<RedirectPage />} />
      </Routes>
    </BrowserRouter>
  );
}
