import './App.css';
function App() {

  const uploadImage = async(event) =>{
    const file = event.target.files[0]; // 파일 선택 시
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:8000/extract-document',{
      method : 'POST',
      body : formData
    });

    const data = await response.json();
    console.log('추출된 데이터 : ', data);
  }

  return (
<div style={{ padding: '20px' }}>
      <h2>문서 데이터 추출</h2>
      <input type="file" onChange={uploadImage} />
    </div>
  );
}

export default App;
