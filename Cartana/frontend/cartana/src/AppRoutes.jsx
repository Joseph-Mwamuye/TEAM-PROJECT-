import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "./Pages/Home";
import ResultPage from "./Pages/ResultPage";
import SearchPage from "./Pages/SearchPage";
import SignIn from "./Pages/SignIn";
import SignUp from "./Pages/SignUp";




import React from 'react'

const AppRoutes = () => {
  return (

    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="resultpage" element={<ResultPage />} />
        <Route path="searchpage" element={<SearchPage />} />
        <Route path="signin" element={<SignIn />} />
        <Route path="signup" element={<SignUp />} />

        
      </Routes>
    </Router>
    
  )
}

export default AppRoutes