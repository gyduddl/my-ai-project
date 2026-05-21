import { useState } from "react";
import axios from "axios";

export default function Login({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  let env_url =import.meta.env.VITE_API_URL;

  const handleLogin = async () => {
    try {
      const res = await axios.post(`http://${env_url}/login`, 
        {email:email, password:password},
        {withCredentials:true}
      );
      window.location.href = "/mainpage"; //reload를 하여 네트워크 탭 기록 안남게
    } catch (e) {
      setError("이메일 또는 비밀번호가 틀렸습니다.");
    }
  };

  const handleRegister = async () => {
    try {
      await axios.post(`http://${env_url}/register`, { email, password });
      setIsRegister(false);
      setError("회원가입 완료! 로그인해주세요.");
      window.location.href="/"
    } catch (e) {
      setError(e.response?.data?.detail || "회원가입 실패");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "100px auto", display: "flex", flexDirection: "column", gap: 12 }}>
      <h2>{isRegister ? "회원가입" : "로그인"}</h2>
      <input
        type="email" placeholder="이메일"
        value={email} onChange={e => setEmail(e.target.value)}
      />
      <input
        type="password" placeholder="비밀번호"
        value={password} onChange={e => setPassword(e.target.value)}
      />
      {error && <p style={{ color: "red" }}>{error}</p>}
      <button onClick={isRegister ? handleRegister : handleLogin}>
        {isRegister ? "회원가입" : "로그인"}
      </button>
      <button onClick={() => { setIsRegister(!isRegister); setError(""); }}>
        {isRegister ? "로그인으로" : "회원가입으로"}
      </button>
    </div>
  );
}