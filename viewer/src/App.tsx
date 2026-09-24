import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Header } from "./components/Header";
import { HomePage } from "./pages/HomePage";
import { SearchPage } from "./pages/SearchPage";
import { ShowDetailPage } from "./pages/ShowDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main className="viewer-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/shows/:slug" element={<ShowDetailPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}