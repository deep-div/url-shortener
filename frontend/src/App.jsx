import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NavBar from './components/Navbar.jsx';
import HomePage from './pages/HomePage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/analytics/:code" element={<AnalyticsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
