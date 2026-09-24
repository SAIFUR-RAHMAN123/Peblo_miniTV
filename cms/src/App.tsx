import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { ShowsListPage } from "./pages/ShowsListPage";
import { ShowFormPage } from "./pages/ShowFormPage";
import { EpisodeFormPage } from "./pages/EpisodeFormPage";
import { PublishPage } from "./pages/PublishPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/shows" replace />} />
          <Route path="/shows" element={<ShowsListPage />} />
          <Route path="/shows/:id" element={<ShowFormPage />} />
          <Route path="/shows/:showId/episodes/new" element={<EpisodeFormPage />} />
          <Route path="/episodes/:id" element={<EpisodeFormPage />} />
          <Route path="/publish" element={<PublishPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}