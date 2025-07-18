# MaterialX Physically Based Shading Nodes

```
Version 1.
Niklas Harrysson - ​Autodesk
Doug Smythe - Industrial Light & Magic
Jonathan Stone - Lucasfilm Advanced Development Group
February 2, 2021
```
# Introduction

The MaterialX Specification describes a number of standard nodes that may be used to construct node
graphs for the processing of images, procedurally-generated values, coordinates and other data. With
the addition of user-defined custom nodes, it is possible to describe complete rendering shaders using
node graphs. Up to this point, there has been no standardization of the specific shader-semantic nodes
used in these node graph shaders, although with the widespread shift toward physically-based shading, it
appears that the industry is settling upon a number of specific BSDF and other functions with
standardized parameters and functionality.
This document describes a number of shader-semantic nodes implementing widely-used surface
scattering, emission and volume distribution functions and utility nodes useful is constructing complex
layered rendering shaders using node graphs. These nodes in combination with other nodes may be used
with the MaterialX shader generation (ShaderGen^1 ) system.

(^1) https://github.com/materialx/MaterialX/blob/master/documents/DeveloperGuide/ShaderGeneration.md


## Table of Contents

- Physical Material Model
   - Scope
   - Physically Plausible Materials
   - Quantities and Units
   - Color Management
   - Surfaces
      - Layering
      - Bump/Normal Mapping
      - Surface Thickness
   - Volumes
   - Lights
- MaterialX PBS Library
   - Data Types
   - BSDF Nodes
   - EDF Nodes
   - VDF Nodes
   - Shader Nodes
   - Utility Nodes
- Shading Model Examples
   - Autodesk Standard Surface
   - UsdPreviewSurface


## Physical Material Model

This section describes the material model used in the MaterialX Physically Based Shading (PBS) library
and the rules we must follow to be physically plausible.

### Scope

A material describes the properties of a surface or medium that involves how it reacts to light. To be
efficient, a material model is split into different parts, where each part handles a specific type of light
interaction: light being scattered at the surface, light being emitted from a surface, light being scattered
inside a medium, etc. The goal of our material model definition is to describe light-material interactions
typical for physically plausible rendering systems, including those in feature film production, real-time
preview, and game engines.
Our model has support for surface materials, which includes scattering and emission of light from the
surface of objects, and volume materials, which includes scattering and emission of light within a
participating medium. For lighting, we support local lights and distant light from environments.
Geometric modification is supported in the form of bump and normal mapping as well as displacement
mapping.

### Physically Plausible Materials

The initial requirements for a physically-plausible material are that it 1) should be energy conserving
and 2) support reciprocity. The energy conserving says that the sum of reflected and transmitted light
leaving a surface must be less than or equal to the amount of light reaching it. The reciprocity
requirement says that if the direction of the traveling light is reversed, the response from the material
remains unchanged. That is, the response is identical if the incoming and outgoing directions are
swapped. All materials implemented for ShaderGen should respect these requirements and only in rare
cases deviate from it when it makes sense for the purpose of artistic freedom.

### Quantities and Units

Radiometric quantities are used by the material model for interactions with the renderer. The
fundamental radiometric quantity is ​ **radiance** ​ (measured in ​ _Wm_ ​ _−2_ ​ _sr_ ​ _−1_ ​) and gives the intensity of light
arriving at, or leaving from, a given point in a given direction. If incident radiance is integrated over all
directions we get ​ **irradiance** ​ (measured in ​ _Wm_ ​ _−2_ ​), and if we integrate this over surface area we get
**power** ​ (measured in ​ _W_ ​). Input parameters for materials and lights specified in photometric units can be
suitably converted to their radiometric counterparts before being submitted to the renderer.
The interpretation of the data types returned by surface and volume shaders are unspecified, and left to
the renderer and the shader generator for that renderer to decide. For an OpenGL-type renderer they will
be tuples of floats containing radiance calculated directly by the shader node, but for an OSL-type
renderer they may be closure primitives that are used by the renderer in the light transport simulation.


In general, a color given as input to the renderer is considered to represent a linear RGB color space.
However, there is nothing stopping a renderer from interpreting the color type differently, for instance to
hold spectral values. In that case, the shader generator for that renderer needs to handle this in the
implementation of the nodes involving the color type.

### Color Management

MaterialX supports the use of color management systems to associate colors with specific color spaces.
A MaterialX document typically specifies the working color space that is to be used for the document as
well as the color space in which input values and textures are given. If these color spaces are different
from the working color space, it is the application's and shader generator's responsibility to transform
them.
The ShaderGen module has an interface that can be used to integrate support for different color
management systems. A simplified implementation with some popular and commonly used color
transformations are supplied and enabled by default. A full integration of OpenColorIO
(​http://opencolorio.org​) is planned for the future.

### Surfaces

In our surface shading model the scattering and emission of light is controlled by distribution functions.
Incident light can be reflected off, transmitted through, or absorbed by a surface. This is represented by a
Bidirectional Scattering Distribution Function (BSDF). Light can also be emitted from a surface, for
instance from a light source or glowing material. This is represented by an Emission Distribution
Function (EDF). The PBS library introduces the data types ​BSDF​ and ​EDF​ to represent the distribution
functions, and there are nodes for constructing, combining and manipulating them.


Another important property is the ​ **index of refraction** ​ (IOR), which describes how light is propagated
through a medium. It controls how much a light ray is bent when crossing the interface between two
media of different refractive indices. It also determines the amount of light that is reflected and
transmitted when reaching the interface, as described by the Fresnel equations.
A surface shader is represented with the data type ​surfaceshader​. In the PBS library there are nodes
that construct a ​surfaceshader​ from a ​BSDF​ and an ​EDF​. Since there are nodes to combine and
modify them, you can easily build surface shaders from different combinations of distribution functions.
Inputs on the distribution function nodes can be connected, and nodes from the standard library can be


combined into complex calculations, giving flexibility for the artist to author material variations over the
surfaces.

#### Layering

In order to simplify authoring of complex materials, our model supports the notion of layering. Typical
examples include: adding a layer of clear coat over a car paint material, or putting a layer of dirt or rust
over a metal surface. Layering can be done in a number of different ways:
● Horizontal Layering: A simple way of layering is using per-shading-point linear mixing of
different BSDFs where a mix factor is given per BSDF controlling its contribution. Since the
weight is calculated per shading point it can be used as a mask to hide contributions on different
parts of a surface. The weight can also be calculated dependent on view angle to simulate
approximate Fresnel behavior. This type of layering can be done both on a BSDF level and on a
surface shader level. The latter is useful for mixing complete shaders which internally contain
many BSDFs, e.g. to put dirt over a car paint, grease over a rusty metal or adding decals to a
plastic surface. We refer to this type of layering as ​ **horizontal layering** ​ and the various <mix>
nodes in the PBS library can be used to achieve this (see below).
● Vertical Layering: A more physically correct form of layering is also supported where a top
BSDF layer is placed over another base BSDF layer, and the light not reflected by the top layer
is assumed to be transmitted to the base layer; for example, adding a dielectric coating layer over
a substrate. The refraction index and roughness of the coating will then affect the attenuation of
light reaching the substrate. The substrate can be a transmissive BSDF to transmit the light
further, or a reflective BSDF to reflect the light back up through the coating. The substrate can in
turn be a reflective BSDF to simulate multiple specular lobes. We refer to this type of layering as
**vertical layering** ​ and it can be achieved using the <layer> node in the PBS library. See
<dielectric_bsdf>, <sheen_bsdf> and <thin_film_bsdf> below.
● Shader Input Blending: Calculating and blending many BSDFs or separate surface shaders can
be expensive. In some situations good results can be achieved by blending the texture/value
inputs instead, before any illumination calculations. Typically one would use this with an
über-shader that can simulate many different materials, and by masking or blending its inputs
over the surface you get the appearance of having multiple layers, but with less expensive texture
or value blending. Examples of this are given in the main MaterialX Specification "pre-shader
compositing" example.

#### Bump/Normal Mapping

The surface normal used for shading calculations is supplied as input to each BSDF that requires it. The
normal can be perturbed by bump or normal mapping, before it is given to the BSDF. As a result, one
can supply different normals for different BSDFs for the same shading point. When layering BSDFs,
each layer can use different bump and normal maps.


#### Surface Thickness

It is common for shading models to differentiate between thick and thin surfaces. We define a ​ **thick
surface** ​ as an object where the surface represents a closed watertight interface with a solid interior made
of the same material. A typical example is a solid glass object. A ​ **thin surface** ​ on the other hand is
defined as an object which doesn’t have any thickness or volume, such as a tree leaf or a sheet of paper.
For a thick surface there is no backside visible if the material is opaque. If a backside is hit by accident
in this case, the shader should return black to avoid unnecessary computations and possible light
leakage. In the case of a transparent thick surface, a backside hit should be treated as light exiting the
closed interface. For a thin surface both the front and back side are visible and it can have different
materials on each side. If the material is transparent in this case the thin wall makes the light transmit
without refracting, like a glass window or bubble.
Two nodes in our material model are used to construct surface shaders for these cases. The <surface>
node constructs thick surfaces and is the main node to use since most objects around us have thick
surfaces. The <thin_surface> node may be used to construct thin surfaces, and here a different BSDF
and EDF may be set on each side. See the ​ **Shader Nodes** ​ section below for more information.

### Volumes

In our volume shader model the scattering of light in a participating medium is controlled by a volume
distribution function (VDF), with coefficients controlling the rate of absorption and scattering. The VDF
represents what physicists call a ​ _phase function,_ ​describing how the light is distributed from its current
direction when it is scattered in the medium. This is analogous to how a BSDF describes scattering at a
surface, but with one important difference: a VDF is normalized, summing to 1.0 if all directions are
considered. Additionally, the amount of absorption and scattering is controlled by coefficients that gives
the rate (probability) per distance traveled in world space. The ​ **absorption coefficient** ​ sets the rate of
absorption for light traveling through the medium, and the ​ **scattering coefficient** ​ sets the rate of which
the light is scattered from its current direction. The unit for these are ​ _m_ ​ _−1_ ​.
Light can also be emitted from a volume. This is represented by an EDF analog to emission from
surfaces, but in this context the emission is given as radiance per distance traveled through the medium.
The unit for this is ​ _Wm_ ​ _−3_ ​ _sr_ ​ _−1_ ​. The emission distribution is oriented along the current direction.
The <volume> node in the PBS library constructs a volume shader from individual VDF and EDF
components. There are also nodes to construct various VDFs, as well as nodes to combine them to build
more complex ones.
VDFs can also be used to describe the interior of a surface. A typical example would be to model how
light is absorbed or scattered when transmitted through colored glass or turbid water. This is done by
layering a BSDF for the surface transmission over the VDF using a <layer> node.


### Lights

Light sources can be divided into environment lights and local lights. Environment lights represent
contributions coming from infinitely far away. All other lights are local lights and have a position and
extent in space.
Local lights are specified as light shaders assigned to a locator, modeling an explicit light source, or in
the form of emissive geometry using an emissive surface shader. The <light> node in the PBS library
constructs a light shader from an EDF. There are also nodes to construct various EDFs as well as nodes
to combine them to build more complex ones. Emissive properties of surface shaders are also modelled
using EDFs; see the ​ **EDF Nodes** ​ section below for more information.
Light contributions coming from far away are handled by environment lights. These are typically
photographically-captured or procedurally-generated images that surround the whole scene. This
category of lights also includes sources like the sun, where the long distance traveled makes the light
essentially directional and without falloff. For all shading points, an environment is seen as being
infinitely far away. Environments are work in progress and not yet defined in the PBS library.


## MaterialX PBS Library

MaterialX includes a library of types and nodes for creating physically plausible materials and lights as
described above. This section outlines the content of that library.

### Data Types

● BSDF​: Data type representing a Bidirectional Scattering Distribution Function.
● EDF​: Data type representing an Emission Distribution Function.
● VDF​: Data type representing a Volume Distribution Function.
The PBS nodes also make use of the following standard MaterialX types:
● surfaceshader​: Data type representing a surface shader.
● lightshader​: Data type representing a light shader.
● volumeshader​: Data type representing a volume shader.
● displacementshader​: Data type representing a displacement shader.

### BSDF Nodes

```
● oren_nayar_diffuse_bsdf ​: Constructs a diffuse reflection BSDF based on the
Oren-Nayar reflectance model^2. A roughness of 0.0 gives Lambertian reflectance.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ color​ (color3): Diffuse reflectivity (albedo). Defaults to (0.18, 0.18, 0.18).
○ roughness ​(float): Surface roughness, range [0.0, 1.0]. Defaults to 0.0.
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
● burley_diffuse_bsdf ​: Constructs a diffuse reflection BSDF based on the corresponding
component of the Disney Principled model^3.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ color​ (color3): Diffuse reflectivity (albedo). Defaults to (0.18, 0.18, 0.18).
○ roughness​ (float): Surface roughness, range [0.0, 1.0]. Defaults to 0.0.
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
● dielectric_bsdf ​: Constructs a reflection and/or transmission BSDF based on a microfacet
reflectance model and a Fresnel curve for dielectrics^4. If reflection scattering is enabled the node
may be layered vertically over a base BSDF for the surface beneath the dielectric layer. By
chaining multiple <dielectric_bsdf> nodes you can describe a surface with multiple specular
lobes. If transmission scattering is enabled the node may be layered over a VDF describing the
```
(^2) M. Oren, S.K. Nayar, Diffuse reflectance from rough surfaces, https://ieeexplore.ieee.org/abstract/document/341163, 1993
(^3) Brent Burley, Physically-Based Shading at Disney,
https://disney-animation.s3.amazonaws.com/library/s2012_pbs_disney_brdf_notes_v2.pdf, 2012
(^4) Bruce Walter et al., Microfacet Models for Refraction through Rough Surfaces,
https://www.cs.cornell.edu/~srm/publications/EGSR07-btdf.pdf, 2007


```
surface interior to handle absorption and scattering inside the medium, useful for colored glass,
turbid water, etc.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ tint​ (color3): Color weight to tint the reflected and transmitted light. Defaults to (1.0, 1.0,
1.0). Note that changing the tint gives non-physical results and should only be done when
needed for artistic purposes.
○ ior​ (float): Index of refraction of the surface. Defaults to 1.5. If set to 0.0 the Fresnel curve
is disabled and reflectivity is controlled only by weight and tint.
○ roughness​ (vector2): Surface roughness. Defaults to (0.0, 0.0).
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
○ tangent​ (vector3): Tangent vector of the surface. Defaults to world space tangent.
○ distribution​ (uniform string): Microfacet distribution type. Defaults to "ggx".
○ scatter_mode​ (uniform string): Scattering mode, specifying whether the BSDF supports
reflection "R", transmission "T" or both reflection and transmission "RT". With "RT",
reflection and transmission occur both when entering and leaving a surface, with their
respective intensities controlled by the Fresnel curve. Depending on the IOR and incident
angle, it is possible for total internal reflection to occur, generating no transmission even if
"T" or "RT" is selected. Defaults to "R".
● conductor_bsdf ​: Constructs a reflection BSDF based on a microfacet reflectance model^5.
Uses a Fresnel curve with complex refraction index for conductors/metals. If an artistic
parametrization^6 is needed the <artistic_ior> utility node can be connected to handle this.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ ior ​(color3): Index of refraction. Default is (0.18, 0.42, 1.37) with colorspace "none"
(approximate IOR for gold).
○ extinction​ (color3): Extinction coefficient. Default is (3.42, 2.35, 1.77) with colorspace
"none" (approximate extinction coefficients for gold).
○ roughness​ (vector2): Surface roughness. Defaults to (0.0, 0.0).
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
○ tangent​ (vector3): Tangent vector of the surface. Defaults to world space tangent.
○ distribution​ (uniform string): Microfacet distribution type. Defaults to "ggx".
● generalized_schlick_bsdf ​: Constructs a reflection and/or transmission BSDF based on
a microfacet model and a generalized Schlick Fresnel curve^7. If reflection scattering is enabled
the node may be layered vertically over a base BSDF for the surface beneath the dielectric layer.
By chaining multiple <generalized_schlick_bsdf> nodes you can describe a surface with multiple
specular lobes. If transmission scattering is enabled the node may be layered over a VDF
describing the surface interior to handle absorption and scattering inside the medium, useful for
colored glass, turbid water, etc.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ color0​ (color3): Reflectivity per color component at facing angles. Defaults to (1.0, 1.0,
1.0).
```
(^5) Brent Burley, Physically-Based Shading at Disney,
https://disney-animation.s3.amazonaws.com/library/s2012_pbs_disney_brdf_notes_v2.pdf​, 2012
(^6) Ole Gulbrandsen, Artist Friendly Metallic Fresnel. [http://jcgt.org/published/0003/04/03/paper.pdf,](http://jcgt.org/published/0003/04/03/paper.pdf,) 2014
(^7) Sony Pictures Imageworks, Revisiting Physically Based Shading at Imageworks,
https://blog.selfshadow.com/publications/s2017-shading-course/imageworks/s2017_pbs_imageworks_slides.pdf.


```
○ color90​ (color3): Reflectivity per color component at grazing angles. Defaults to (1.0, 1.0,
1.0).
○ exponent​ (float): Exponent for the Schlick blending between color0 and color90. Defaults
to 5.0.
○ roughness​ (vector2): Surface roughness. Defaults to (0.0, 0.0).
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
○ tangent​ (vector3): Tangent vector of the surface. Defaults to world space tangent.
○ distribution​ (uniform string): Microfacet distribution type. Defaults to "ggx".
○ scatter_mode​ (uniform string): Scattering mode, specifying whether the BSDF supports
reflection "R", transmission "T" or both reflection and transmission "RT". With "RT",
reflection and transmission occur both when entering and leaving a surface, with their
respective intensities controlled by the Fresnel curve. Depending on the IOR and incident
angle, it is possible for total internal reflection to occur, generating no transmission even if
"T" or "RT" is selected. Defaults to "R".
● translucent_bsdf ​: Constructs a translucent (diffuse transmission) BSDF based on the
Lambert reflectance model.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ color​ (color3): Diffuse transmittance. Defaults to (1.0, 1.0, 1.0).
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
● subsurface_bsdf ​: Constructs a subsurface scattering BSDF for subsurface scattering within
a homogeneous medium. The parameterization is chosen to match random walk Monte Carlo
methods as well as approximate empirical methods^8. Note that this category of subsurface
scattering can be defined more rigorously as a BSDF vertically layered over an
<anisotropic_vdf>, and we expect these two descriptions of the scattering-surface distribution
function to be unified in future versions of MaterialX.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ color​ (color3): Diffuse reflectivity (albedo). Defaults to (0.18, 0.18, 0.18).
○ radius​ (color3): Sets the average distance that light might propagate below the surface
before scattering back out. This is also known as the mean free path of the material. The
radius can be set for each color component separately. Default is (1, 1, 1).
○ anisotropy​ (float): Anisotropy factor, controlling the scattering direction, range [-1.0,
1.0]. Negative values give backwards scattering, positive values give forward scattering, and
a value of zero gives uniform scattering. Defaults to 0.0.
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
● sheen_bsdf ​: Constructs a microfacet BSDF for the back-scattering properties of cloth-like
materials. This node may be layered vertically over a base BSDF using a <layer> node. All
energy that is not reflected will be transmitted to the base layer^9.
○ weight​ (float): Weight for this BSDF’s contribution, range [0.0, 1.0]. Defaults to 1.0.
○ color​ (color3): Sheen reflectivity. Defaults to (1.0, 1.0, 1.0).
○ roughness​ (float): Surface roughness, range [0.0, 1.0]. Defaults to 0.2.
```
(^8) Pixar, Approximate Reflectance Profiles for Efficient Subsurface Scattering,
[http://graphics.pixar.com/library/ApproxBSSRDF/.](http://graphics.pixar.com/library/ApproxBSSRDF/.) 2015
(^9) Sony Pictures Imageworks, Production Friendly Microfacet Sheen BRDF,
https://blog.selfshadow.com/publications/s2017-shading-course/imageworks/s2017_pbs_imageworks_sheen.pdf


```
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
● thin_film_bsdf ​: Adds an iridescent thin film layer over a microfacet base BSDF^10. This
must be layered over another base BSDF using a <layer> node, as the node is a modifier and
cannot be used as a standalone BSDF.
○ thickness​ (float): Thickness of the thin film layer in nanometers. Default is 1000 nm.
○ ior​ (float): Index of refraction of the thin film layer. Default is 1.5.
```
### EDF Nodes

```
● uniform_edf ​: Constructs an EDF emitting light uniformly in all directions.
○ color​ (color3): Radiant emittance of light leaving the surface. Default is (1, 1, 1).
● conical_edf ​: Constructs an EDF emitting light inside a cone around the normal direction.
○ color​ (color3): Radiant emittance of light leaving the surface. Default is (1, 1, 1).
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
○ inner_angle​ (uniform float): Angle of inner cone where intensity falloff starts (given in
degrees). Defaults to 60.
○ outer_angle​ (uniform float): Angle of outer cone where intensity goes to zero (given in
degrees). If set to a smaller value than inner angle no falloff will occur within the cone.
Defaults to 0.
● measured_edf ​: Constructs an EDF emitting light according to a measured IES light profile^11.
○ color​ (color3): Radiant emittance of light leaving the surface. Default is (1, 1, 1).
○ normal​ (vector3): Normal vector of the surface. Defaults to world space normal.
○ file​ (uniform filename): Path to a file containing IES light profile data. Default is "".
```
### VDF Nodes

```
● absorption_vdf ​: Constructs a VDF for pure light absorption.
○ absorption​ (color3): Absorption rate for the medium (rate per distance traveled in the
medium, given in ​ m ​ −1 ​). Set for each color component/wavelength separately. Default is (0, 0,
0).
● anisotropic_vdf ​: Constructs a VDF scattering light for a participating medium, based on
the Henyey-Greenstein phase function^12. Forward, backward and uniform scattering is supported
and controlled by the anisotropy input.
○ absorption​ (color3): Absorption rate for the medium (rate per distance traveled in the
medium, given in ​ m ​ −1 ​). Set for each color component/wavelength separately.
```
(^10) Laurent Belcour, Pascal Barla, A Practical Extension to Microfacet Theory for the Modeling of Varying Iridescence,
https://belcour.github.io/blog/research/2017/05/01/brdf-thin-film.html, 2017
(^11) Standard File Format for Electronic Transfer of Photometric Data,
https://www.ies.org/product/standard-file-format-for-electronic-transfer-of-photometric-data/
(^12) Matt Pharr, Wenzel Jakob, Greg Humphreys, Physically Based Rendering: From Theory To Implementation, Chapter 11.2,
[http://www.pbr-book.org/3ed-2018/Volume_Scattering/Phase_Functions.html](http://www.pbr-book.org/3ed-2018/Volume_Scattering/Phase_Functions.html)


```
Default is (0, 0, 0).
○ scattering​ (color3): Scattering rate for the medium (rate per distance traveled in the
medium, given in ​ m ​ −1 ​). Set for each color component/wavelength separately. Default is (0, 0,
0).
○ anisotropy​ (float): Anisotropy factor, controlling the scattering direction, range [-1.0,
1.0]. Negative values give backwards scattering, positive values give forward scattering, and
a value of 0.0 (the default) gives uniform scattering.
```
### Shader Nodes

```
● surface ​: Constructs a surface shader describing light scattering and emission for closed
”thick” objects. If the BSDF is opaque only the front side will reflect light and back sides will be
black if visible. If the BSDF is transmissive the surface will act as an interface to a solid volume
made from this material. Output type "surfaceshader".
○ bsdf​ (BSDF): Bidirectional scattering distribution function for the surface. Default is "".
○ edf​ (EDF): Emission distribution function for the surface. If unconnected, then no emission
will occur.
○ opacity​ (float): Cutout opacity for the surface. Default to 1.0.
● thin_surface ​: Constructs a surface shader describing light scattering and emission for
non-closed ”thin” objects. The surface is two sided and can describe a different BSDF and EDF
for each side. If only one BSDF is connected the same BSDF will be used on both sides. If an
EDF is not connected no emission will occur from that side. Volumetric properties of connected
BSDF’s are not supported since the object has no volume. Output type "surfaceshader".
○ front_bsdf​ (BSDF): Bidirectional scattering distribution function for the front side.
Default is "".
○ front_edf​ (EDF): Emission distribution function for the front side. Default is no emission.
○ back_bsdf​ (BSDF): Bidirectional scattering distribution function for the back side. If not
provided, the ​front_bsdf​ BSDF will be used for both sides.
○ back_edf​ (EDF): Emission distribution function for the back side. Default is no emission.
○ opacity​ (float): Cutout opacity for the surface. Default to 1.0.
● volume ​: Constructs a volume shader describing a participating medium. Output type
"volumeshader".
○ vdf​ (VDF): Volume distribution function for the medium. Default is "".
○ edf​ (EDF): Emission distribution function for the medium. If unconnected, then no
emission will occur.
● light ​: Constructs a light shader describing an explicit light source. The light shader will emit
light according to the connected EDF. If the shader is attached to geometry both sides will be
considered for light emission and the EDF controls if light is emitted from both sides or not.
Output type "lightshader".
○ edf​ (EDF): Emission distribution function for the light source. Default is no emission.
○ intensity​ (color3): Intensity multiplier for the EDF’s emittance. Default to (1.0, 1.0, 1.0).
○ exposure​ (float): Exposure control for the EDF’s emittance. Default to 0.0.
```

```
● displacement ​: Constructs a displacement shader describing geometric modification to
surfaces. Output type "displacementshader".
○ displacement​ (float or vector3): Scalar (along the surface normal direction) or vector
displacement (in (dPdu, dPdv, N) tangent/normal space) for each position. Default is 0.
○ scale​ (float): Scale factor for the displacement vector. Default is 1.0.
```
### Utility Nodes

```
● mix ​: Mix two same-type distribution functions according to a weight. Performs horizontal
layering by linear interpolation between the two inputs, using the function "bg∗(1−mix) +
fg∗mix".
○ bg​ (BSDF or EDF or VDF): The first distribution function. Defaults to "".
○ fg​ (same type as ​bg​): The second distribution function. Defaults to "".
○ mix​ (float): The mixing weight, range [0.0, 1.0]. Default is 0.
● layer ​: Vertically layer a layerable BSDF such as ​dielectric_bsdf​,
generalized_schlick_bsdf​, ​sheen_bsdf​ or ​thin_film_bsdf​ over a BSDF or VDF.
The implementation is target specific, but a standard way of handling this is by albedo scaling,
using the function "base*(1-reflectance(top)) + top", where the reflectance function calculates
the directional albedo of a given BSDF.
○ top​ (BSDF): The top BSDF. Defaults to "".
○ base​ (BSDF or VDF): The base BSDF or VDF. Defaults to "".
● add ​: Additively blend two distribution functions of the same type.
○ in1​ (BSDF or EDF or VDF): The first distribution function. Defaults to "".
○ in2​ (same type as ​in1​): The second distribution function. Defaults to "".
● multiply ​: Multiply the contribution of a distribution function by a scaling weight. The weight
is either a float to attenuate the channels uniformly, or a color which can attenuate the channels
separately. To be energy conserving the scaling weight should be no more than 1.0 in any
channel.
○ in1​ (BSDF or EDF or VDF): The distribution function to scale. Defaults to "".
○ in2​ (float or color3): The scaling weight. Default is 1.0.
● roughness_anisotropy ​: Calculates anisotropic surface roughness from a scalar roughness
and anisotropy parameterization. An anisotropy value above 0.0 stretches the roughness in the
direction of the surface's "tangent" vector. An anisotropy value of 0.0 gives isotropic roughness.
The roughness value is squared to achieve a more linear roughness look over the input range
[0,1]. Output type "vector2".
○ roughness​ (float): Roughness value, range [0.0, 1.0]. Defaults to 0.0.
○ anisotropy​ (float): Amount of anisotropy, range [0.0, 1.0]. Defaults to 0.0.
● roughness_dual ​: Calculates anisotropic surface roughness from a dual surface roughness
parameterization. The roughness is squared to achieve a more linear roughness look over the
input range [0,1]. Output type "vector2".
○ roughness​ (vector2): Roughness in x and y directions, range [0.0, 1.0]. Defaults to (0.0,
```

##### 0.0).

● **glossiness_anisotropy** ​: Calculates anisotropic surface roughness from a scalar
glossiness and anisotropy parameterization. This node gives the same result as roughness
anisotropy except that the glossiness value is an inverted roughness value. To be used as a
convenience for shading models using the glossiness parameterization. Output type "vector2".
○ glossiness​ (float): Roughness value, range [0.0, 1.0]. Defaults to 0.0.
○ anisotropy​ (float): Amount of anisotropy, range [0.0, 1.0]. Defaults to 0.0.
● **blackbody** ​: Returns the radiant emittance of a blackbody radiator with the given temperature.
Output type "color3".
○ temperature​ (float): Temperature in Kelvin. Default is 5000.
● **artistic_ior** ​: Converts the artistic parameterization reflectivity and edge_color to complex
IOR values. To be used with the <conductor_bsdf> node.
○ reflectivity​ (color3): Reflectivity per color component at facing angles. Default is
(0.947, 0.776, 0.371).
○ edge_color​ (color3): Reflectivity per color component at grazing angles. Default is (1.0,
0.982, 0.753).
○ ior​ (​ **output** ​, vector3): Computed index of refraction.
○ extinction​ (​ **output** ​, vector3): Computed extinction coefficient.


## Shading Model Examples

This section contains examples of shading model implementations using the MaterialX PBS library. For
all examples, the shading model is defined via a <nodedef> interface plus a nodegraph implementation.
The resulting nodes can be used as shaders by a MaterialX material definition.

### Autodesk Standard Surface

This is a surface shading model used in Autodesk products created by the Solid Angle team for the
Arnold renderer. It is an über shader built from ten different BSDF layers^13.
A MaterialX definition and nodegraph implementation of Autodesk Standard Surface can be found here:
https://github.com/Autodesk/standard-surface/blob/master/reference/standard_surface.mtlx

### UsdPreviewSurface

This is a shading model proposed by Pixar for USD^14. It is meant to model a physically based surface
that strikes a balance between expressiveness and reliable interchange between current day DCC’s and
game engines and other real-time rendering clients.
A MaterialX definition and nodegraph implementation of UsdPreviewSurface can be found here:
https://github.com/materialx/MaterialX/blob/master/libraries/bxdf/usd_preview_surface.mtlx

(^13) Autodesk, A Surface Standard, https://github.com/Autodesk/standard-surface, 2019.
(^14) Pixar, UsdPreviewSurface Proposal. https://graphics.pixar.com/usd/docs/UsdPreviewSurface-Proposal.html, 2018.


