import React from 'react'
import "./HeroSection.css";
import HeroImage from "./HomeImageAssets/computer-girl.png"

const HeroSection = () => {
  return (
    <>
    <section className="hero">
            <div className="hero-content">
                <h1>Find any product on the internet with <span>Cartana</span></h1>
                <p>Tired of doom-scrolling through e-commerce sites to find a product that fits your budget? Cartana has your back.</p>
                <div className="cta-buttons">
                    <button className="try-it-out">Try it out</button>
                    <button className="create-account">Create your Cartana account</button>
                </div>
            </div>
            <div className="hero-image">
                <img src={HeroImage} alt="Person using Cartana on a computer" />
            </div>
        </section>
    
    </>
  )
}

export default HeroSection