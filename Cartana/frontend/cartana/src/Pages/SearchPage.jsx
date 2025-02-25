import React from 'react'
import NavBar from '../components/NavBar'
import SearchIcon from "./PagesImageAssets/mingcute_search-fill.svg"
import "./SearchPage.css"

const SearchPage = () => {
  return (
    <>
    <NavBar />
    <main>
    <section className="search-area">
            <h1>Start here. What product are you searching for?</h1>
            <div className="search-box">
                <span className="search-icon">
                    <img src={SearchIcon} alt="Search Icon"/> </span>
                <input type="text" placeholder="Try JBL headphones"/>
            </div>
            <button className="search-button">Search Cartana</button>
        </section>
        </main>
    </>
  )
}

export default SearchPage