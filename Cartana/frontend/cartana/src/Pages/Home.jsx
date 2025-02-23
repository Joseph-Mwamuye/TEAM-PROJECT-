import React from "react";
import NavBar from "../components/NavBar";
import HeroSection from "../sections/HomePageSections/HeroSection";
import LogoCard from "../sections/HomePageSections/LogoCard";
import Footer from "../components/Footer";

const Home = () => {
  return (
    <>
      <NavBar />
      <HeroSection />
      <LogoCard />
      <Footer />
    </>
  );
};

export default Home;
