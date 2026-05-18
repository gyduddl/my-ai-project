import { useState, ChangeEvent } from "react";
import axios, { AxiosError } from "axios";
import { useNavigate } from "react-router-dom";

// 1. 컴포넌트 Props 타입 정의
interface LoginProps {
  onLoginSuccess?: () => void;
}

// 2. 백엔드 에러 응답 데이터 구조 정의 (FastAPI 등에서 주로 사용하는 형태)
interface ErrorResponse {
  detail?: string;
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");

  // 3. 로그인 핸들러 타입 적용
  const handleLogin = async (): Promise<void> => {
    try {
      // 필요하다면 이곳에서 온로그인성공 함수를 호출할 수 있습니다. 예시: onLoginSuccess?.();
      await axios.post(
        "http://localhost:8000/login",
        { email, password },
        { withCredentials: true }
      );
      navigate("/mainpage");
    } catch (e) {
      setError("이메일 또는 비밀번호가 틀렸습니다.");
    }
  };

  // 4. 회원가입 핸들러 타입 및 Axios 에러 타입 구체화
  const handleRegister = async (): Promise<void> => {
    try {
      await axios.post("http://localhost:8000/register", { email, password });
      setIsRegister(false);
      setError("회원가입 완료! 로그인해주세요.");
    } catch (e) {
      // Axios 에러인지 확인하고 정확한 제네릭 타입 지정
      if (axios.isAxiosError(e)) {
        const axiosError = e as AxiosError<ErrorResponse>;
        setError(axiosError.response?.data?.detail || "회원가입 실패");
      } else {
        setError("알 수 없는 오류가 발생했습니다.");
      }
    }
  };

  // 5. Input 변경 이벤트 핸들러 분리 (인라인 가독성 개선)
  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setEmail(e.target.value);
  };

  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setPassword(e.target.value);
  };

  return (
    <div style={{ maxWidth: 400, margin: "100px auto", display: "flex", flexDirection: "column", gap: 12 }}>
      <h2>{isRegister ? "회원가입" : "로그인"}</h2>
      <input
        type="email"
        placeholder="이메일"
        value={email}
        onChange={handleEmailChange}
      />
      <input
        type="password"
        placeholder="비밀번호"
        value={password}
        onChange={handlePasswordChange}
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