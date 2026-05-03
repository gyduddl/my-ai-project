import './App.css';
import React, {useState} from 'react';
import axios from 'axios';

function App() {

  const [diary,setDiary] = useState('')

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

  const handleSumbit = async (event) =>{
    event.preventDefault();
    try{
      const data = { content : diary}
      const response = await axios.post("http://localhost:8000/unrest-check", data);
      console.log(response)
    }catch(error){
      console.error("전송에러",error);
    
      }
  }

  return (
<div style={{ padding: '20px' }}>
      <h2>문서 데이터 추출</h2>
      <input type="file" onChange={uploadImage} />
      <form onSubmit={handleSumbit}>
      <label>
        <input type="text" value={diary} onChange={(e)=> setDiary(e.target.value)}/>
      </label>
      <button type="submit">제출</button>
      </form>
    </div>

  );
}

export default App;
