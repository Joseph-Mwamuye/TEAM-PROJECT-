import React from 'react'
import "./Navbar.css";

const NavBar = () => {
  return (
    <>
        <nav>
            <a href="#" class="logo">Cartana</a>
            <ul>
                <li><a href="#">About</a></li>
                <li><a href="#">Pricing</a></li>
                <li><a href="#">Our Team</a></li>
            </ul>
            <ul>
                <li><a href="#">Help</a></li>
                <li><a href="#">Login</a></li>
                <li><a href="#" class="signup-btn">Sign Up</a></li>
            </ul>
        </nav>
    </>
  )
}

export default NavBar