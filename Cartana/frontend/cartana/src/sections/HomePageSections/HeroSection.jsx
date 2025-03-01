import React from 'react'
import "./HeroSection.css";
import PrimaryButton from '../../components/Buttons/PrimaryButton';
import HeroImage from "./HomeImageAssets/computer-girl.png"

const HeroSection = () => {
  return (
    <>
    <section className="hero">
            <div className="hero-content">
                <h1>Find any product on the internet with <span>Cartana</span></h1>
                <p>Tired of doom-scrolling through e-commerce sites to find a product that fits your budget? Cartana has your back.</p>
                <div className="cta-buttons">
                    <PrimaryButton label="Try it out" className="black-button" navigateTo="/searchpage"/>
                    <PrimaryButton label="Create Cartana Account" className="border-blue-button" navigateTo="/signup"/>

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