import './App.css';
import React, { useState, useEffect } from 'react';
import axios from 'axios';


function MainPage() {
  const [summaryData, setSummaryData] = useState(null); // 서버 응답 데이터 저장
  const [showDropdown, setShowDropdown] = useState(false); // 드롭다운 상태
  const [isProcessing, setIsProcessing] = useState(false);

  const uploadImage = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('length', 'MIDDLE')
    formData.append('style', 'STYLE1')
    

    try {
      const response = await axios.post('http://localhost:8080/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });

      const fileId = response.data.fileId;

      // 2. 상태에 저장 (즉시 다운로드하지 않음)
      setSummaryData({
        fileID: response.data.fileId,
        fileName :response.data.fileName,
        summary:null,
        category:null
    });
      setIsProcessing(true);

      const interval = setInterval(async()=>{
        try{
          const statusRes = await axios.get(`http://localhost:8080/task/${fileId}/progress`,
            {withCredentials:true}
          );
          console.log("잘들어가는지 확인:",statusRes);
          if(statusRes.data.state=="SUCCESS"){
            clearInterval(interval);
            setIsProcessing(false);

            setSummaryData(prev =>({
              ...prev,
              summary:statusRes.data.summary,
              category:statusRes.data.category
            }))
          }

          if (statusRes.data.state === "FAILURE") {
                    clearInterval(interval);
                    setIsProcessing(false);
                    alert("파일 처리 중 오류가 발생했습니다.");
                }
        }catch(e){
          console.error("상태 확인 실패:", e)
        }
      },2000)


    } catch (error) {
      console.error("전송 에러:", error);
      alert("파일 처리 중 오류가 발생했습니다.");
    }
  };

  // 3. 실제 다운로드 실행 함수
  const handleDownload = async(format) => {
    try{
      const response = await axios({
      url: `http://localhost:8080/download/${summaryData.fileId}`,
      method: 'GET',
      params: { format: format },
      responseType: 'blob', // 서버에서 보내는 스트림 데이터를 받기 위해 필수
    });

    // 받은 데이터를 브라우저에서 파일로 인식하게 만듦
    const mimeTypes = {
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
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url); // 메모리 해제
      setShowDropdown(false);
    } catch (error){
      console.error("다운로드 실패:", error);
    }
  };

  useEffect(()=>{
  const fetchHistory = async () => {
    try {
      const response = await axios.get("http://localhost:8080/history", {
        withCredentials: true,
      });
    } catch (e) {
      console.error("이력 조회 실패:", e);
    }
  };

  fetchHistory();
  },[])

  return (
    <div style={{ padding: '30px', textAlign: 'center' }}>
      <h1>📄 AI 문서 요약 서비스</h1>
      <input type="file" onChange={uploadImage} />

      <hr style={{ margin: '30px 0' }} />

      {summaryData && (
        <div style={{ position: 'relative', width: '80%', margin: '0 auto', textAlign: 'left', background: '#fff', padding: '20px', borderRadius: '8px', border: '1px solid #ddd' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>🔍 요약 결과</h3>
            
            {/* 4. 드롭다운 버튼 (⋮) */}
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
                  border: '1px solid #ccc', borderRadius: '5px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', zindexing: 100 
                }}>
                  <div className="dropdown-item" onClick={() => handleDownload('txt')}>TXT 다운로드</div>
                  <div className="dropdown-item" onClick={() => handleDownload('pdf')}>PDF 다운로드</div>
                </div>
              )}
            </div>
          </div>

          <div style={{ marginTop: '10px', whiteSpace: 'pre-wrap', backgroundColor: '#f9f9f9', padding: '15px' }}>
             {/* Blob을 텍스트로 보여주기 위해선 처리 필요 (간단히 summary info 활용) */}
             {summaryData.summary || "내용 받아오는 중"}
          </div>
        </div>
      )}

      {/* 스타일링을 위한 내부 CSS */}
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