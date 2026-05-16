import { Routes, Route } from 'react-router-dom';
import MainPage from './MainPage';
import Login from './Login';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/mainpage" element={<MainPage />} />
    </Routes>
  );
}

export default App;