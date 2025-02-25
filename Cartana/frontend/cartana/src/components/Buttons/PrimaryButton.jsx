import React from 'react'
import { useNavigate } from 'react-router-dom';
import './PrimaryButton.css'

const PrimaryButton = ({label, className, navigateTo}) => {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate(navigateTo);
    };

  return (
    <button className={`base-button ${className}`} onClick={handleClick}>{label}</button>
  );
}

export default PrimaryButton