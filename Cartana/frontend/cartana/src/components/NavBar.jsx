import React from "react";
import "./Navbar.css";
import PrimaryButton from "./Buttons/PrimaryButton";

const NavBar = () => {
  return (
    <>
      <nav>
        <a href="/" class="logo">
          Cartana
        </a>
        <ul className="column-1">
          <li>
            <a href="#">About</a>
          </li>
          <li>
            <a href="#">Pricing</a>
          </li>
          <li>
            <a href="/searchpage">Try Cartana</a>
          </li>
        </ul>
        <ul className="column-2">
          <li>
            <a href="#">Help</a>
          </li>
          <li>
            <a href="/signin">Login</a>
          </li>

          <li>
            <PrimaryButton
              label="Sign Up"
              className="nav-signup-button"
              navigateTo="/signup"
            />
          </li>
        </ul>
      </nav>
    </>
  );
};

export default NavBar;
