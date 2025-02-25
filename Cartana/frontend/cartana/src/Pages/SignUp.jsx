import React from 'react';
import NavBar from '../components/NavBar';
import GoogleLogo from "./PagesImageAssets/devicon_google.svg";
import SplashPhoto from "./PagesImageAssets/splash-basket.png";
import './SignUp.css'; 

const SignUp = () => {
  return (
    <>
      <NavBar />
      <div className="container">
      <div className="signin-box">
        
        {/* Left Image Section */}
        <div className="image-area">
          <img src={SplashPhoto} alt="Cartana Illustration" />
        </div>

        {/* Right Form Section */}
        <div className="form-area">
          <div className="top-text">
            Find your way with <span className="bold-text">Cartana</span>
          </div>

          <h1>Sign Up</h1>
          <p>Sign in with your social account</p>

          {/* Google Sign-In Button */}
          <button className="google-signin">
            <img src={GoogleLogo} alt="Google Icon" className="icon" />
            Sign Up with Google
          </button>

          <p className="or-text">Or continue with email</p>

          {/* Input Fields */}
          <div className="input-field">
            <i className="fas fa-envelope"></i>
            <input type="email" placeholder="Email" />
          </div>

          <div className="input-field">
            <i className="fas fa-lock"></i>
            <input type="password" placeholder="Password" />
          </div>

          <div className="input-field">
            <i className="fas fa-lock"></i>
            <input type="password" placeholder="Confirm Password" />
          </div>

          {/* Sign In Button */}
          <button className="signin-btn">Sign In</button>

          
        </div>
      </div>
    </div>
    </>
  );
};
export default SignUp;
