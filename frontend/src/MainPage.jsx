import './App.css';
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// 1. 요약 데이터 객체 타입 정의
interface SummaryData {
  fileID: string;
  fileName: string;
  summary: string | null;
  category: string | null;
}

// 2. 소켓 객체 타입 정의
interface TaskStatus {
  percent: number,
  state : string
}

// 3. websocket에서 응답 티입 정의
interface WebhookMessage{
  percent:number,
  state: "PENDING"|"SUCCESS"|"FAILURE"|"PROGRESS"|string,
  extracted_text?:string | null,
  summary?: string | null,
  category?: string | null
}


function MainPage() {
  // server url
  const server_url :string= import.meta.env.VITE_API_URL;

  // 상태 타입 지정
  const [summaryData, setSummaryData] = useState<SummaryData>({
  fileID: '',
  fileName: '',
  summary: null,
  category: null,
});
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false); // 처리 중 여부
  const [isProcess, setIsProcess]= useState<TaskStatus>({percent:0, state:""}); // 로딩상태
  const [extractedText, setExtractedText] = useState<string | null>(null); // ocr 이후 추출된 텍스트

  const wsRef = useRef<WebSocket|null>(null)

  // 3. 파일 업로드 핸들러 타입 지정
  const uploadImage = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; // optional chaining으로 안전하게 접근
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('length', 'MIDDLE');
    formData.append('style', 'STYLE1');

     try {
      const response = await axios.post(`http://${server_url}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });

      // const fileId = response.data.fileId;
      const {fileId} = response.data;

      // 2. 상태에 저장 (즉시 다운로드하지 않음)
      setSummaryData({
        fileID: response.data.fileId,
        fileName :response.data.fileName,
        summary:null,
        category:null
    });
      setIsProcessing(true);
      setIsProcess( {percent: 0, state: "PENDING" })

      const ws = new WebSocket(`ws://${server_url}/ws/${fileId}`)
      wsRef.current = ws;

      ws.onerror = (event: Event) => {
        console.error('웹소켓 에러:', event);
        setIsProcessing(false);
        alert("웹소켓 연결 오류가 발생했습니다.");
      };

      ws.onclose = (event: CloseEvent) => {
        console.log('웹소켓 종료:', event.code, event.reason);
      };

      ws.onopen=(event:Event)=>{
          console.log('$$웹소켓 연결$$');
      }

      ws.onmessage = (event:MessageEvent) =>{
        const data = JSON.parse(event.data) as WebhookMessage; //서버에서 메시지 올때마다 실행. json 문자열을 딕셔너리로 변환
        console.log(`data : ${data}, extractedText:${extractedText}`);
        setIsProcess({
          percent : data.percent,
          state : data.state
        })

        if(data.extracted_text){
          setExtractedText(data.extracted_text);
        }

        if(data.state === "SUCCESS"){
          setIsProcessing(false); // 로딩바 숨김
          setSummaryData(prev=>({
            ...prev,
            summary:data.summary ?? null,
            category:data.category ?? null
          }))
          ws.close()
        }
      if(data.state === "FAILURE"){
        setIsProcessing(false);
        alert("파일 처리 중에 오류가 발생했습니다.1.")
        ws.close()
      }
      }

    } catch (error) {
      console.error("전송 에러:", error);
      alert("파일 처리 중 오류가 발생했습니다.2.");
    }
  };


  // 4. 다운로드 핸들러 타입 지정 (format은 'txt' 또는 'pdf')
  const handleDownload = async (format: 'txt' | 'pdf') => {
    if (!summaryData) return;

    try {
      const response = await axios({
        url: `http://${server_url}/download/${summaryData.fileID}`,
        method: 'GET',
        params: { format: format },
        responseType: 'blob',
      });

      const mimeTypes: Record<string, string> = {
        'txt': 'text/plain',
        'pdf': 'application/pdf'
      };

      const blob = new Blob([response.data], { type: mimeTypes[format] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `요약본_${summaryData.fileName}.${format}`);

      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      setShowDropdown(false);
    } catch (error) {
      console.error("다운로드 실패:", error);
    }
  };

  useEffect(() => {
    const fetchHistory = async (): Promise<void> => {
      try {
        await axios.get("{server_url}/history", {
          withCredentials: true,
        });
      } catch (e) {
        console.error("이력 조회 실패:", e);
      }
    };

    fetchHistory();
  }, []);

  return (
    <div style={{ padding: '30px', textAlign: 'center' }}>
      <h1>📄 AI 문서 요약 서비스</h1>
      <input type="file" onChange={uploadImage} disabled={isProcessing} />
      
      {isProcessing && <p>⏳ 문서를 요약 중입니다. 잠시만 기다려주세요...</p>}

      <hr style={{ margin: '30px 0' }} />

      {summaryData.fileID && (
        <div style={{ position: 'relative', width: '80%', margin: '0 auto', textAlign: 'left', background: '#fff', padding: '20px', borderRadius: '8px', border: '1px solid #ddd' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>🔍 요약 결과</h3>
            
            <div style={{ position: 'relative' }}>
              <button 
                onClick={() => setShowDropdown(!showDropdown)}
                style={{ fontSize: '24px', cursor: 'pointer', background: 'none', border: 'none' }}
              >
                ⋮
              </button>

              {showDropdown && (
                <div style={{ 
                  position: 'absolute', right: 0, top: '30px', backgroundColor: '#fff', 
                  border: '1px solid #ccc', borderRadius: '5px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', zIndex: 100 
                }}>
                  <div className="dropdown-item" onClick={() => handleDownload('txt')}>TXT 다운로드</div>
                  <div className="dropdown-item" onClick={() => handleDownload('pdf')}>PDF 다운로드</div>
                </div>
              )}
            </div>
          </div>

          <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', backgroundColor: '#f9f9f9', padding: '15px' }}>
             {summaryData.summary || "내용을 분석하고 있습니다..."}
          </div>
        </div>
      )}

      <style>{`
        .dropdown-item {
          padding: 10px 20px;
          cursor: pointer;
          min-width: 120px;
        }
        .dropdown-item:hover {
          background-color: #f0f0f0;
        }
      `}</style>
    </div>
  );
}

export default MainPage;