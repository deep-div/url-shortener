import { BrowserRouter, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar.jsx';
import HomePage from './pages/HomePage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <p className="footer-text">
          <strong>snip</strong> — every link has a story.
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
        <Route path="/analytics/:code" element={<AnalyticsPage />} />
      </Routes>
      <Footer />
    </BrowserRouter>
  );
}
