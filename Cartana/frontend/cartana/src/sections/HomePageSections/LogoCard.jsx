import React from 'react'
import JumiaLogo from "./HomeImageAssets/JumiaLogo.svg"
import AmazonLogo from "./HomeImageAssets/lineicons_amazon.svg"
import EbayLogo from "./HomeImageAssets/ebay.svg"
import "./LogoCard.css"


const LogoCard = () => {
  return (
    <>
    <section className='features'>
        <h2>Search from top sites</h2>
        <div className='site-logos'>
            <img src={JumiaLogo} alt='jumia logo'/>
            <img src={AmazonLogo} alt='amazon logo'/>
            <img src={EbayLogo} alt='ebay logo'/>


        </div>

    </section>
    
    </>
  )
}

export default LogoCard