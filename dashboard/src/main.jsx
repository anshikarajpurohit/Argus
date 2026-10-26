import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,Routes,Route,Navigate} from 'react-router-dom';
import {getToken} from './api';
import Shell from './components/Shell';
import Login from './pages/Login';
import './style.css';
function Protected() {
  return getToken() ? <Shell /> : <Navigate to="/login" replace />;
}
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<Protected />} />
      </Routes>
    </BrowserRouter>
  );
}
createRoot(document.getElementById('root')).render(<App/>);
