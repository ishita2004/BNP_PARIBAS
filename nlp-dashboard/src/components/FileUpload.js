import React, { useState } from "react";
import { uploadFiles } from "../api";

export default function FileUpload() {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");

  const handleFiles = (e) => setFiles(e.target.files);

  const handleUpload = async () => {
    if (!files.length) return alert("Select files first!");
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("files", file));
    setStatus("Uploading...");
    try {
      const res = await uploadFiles(formData);
      setStatus(res.data.message || JSON.stringify(res.data));
    } catch (err) {
      setStatus("Upload failed: " + err.message);
    }
  };

  return (
    <div>
      <input type="file" multiple onChange={handleFiles} />
      <button onClick={handleUpload}>Upload</button>
      <p>{status}</p>
    </div>
  );
}
